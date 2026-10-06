# Ptrace注入

## 原理介绍

`ptrace` 是 `Linux` 的一个系统调用，全称 `process trace`，它允许一个进程（`tracer`，跟踪者）观察和控制另一个进程（`tracee`，被跟踪者） 原型是 `long ptrace(enum __ptrace_request request, pid_t pid, void *addr, void *data)`，其中 `request` 是操作类型，比如读寄存器、写内存、继续执行，`pid` 是目标进程的 `pid`，`addr` 和 `data` 是操作的地址和数据，具体含义看 `request`

它提供的核心能力是读目标进程的内存、写目标进程的内存、读目标进程的寄存器、写目标进程的寄存器、让目标进程暂停、让目标进程继续、单步执行目标进程、拦截目标进程的系统调用和信号

`ptrace` 注入其实非常简单，就是 `attach` 目标进程让它暂停，保存寄存器，把寄存器改成一次远程调用 `dlopen` 的参数，让它执行 `dlopen` 加载你的 `.so`，`.so` 里的构造函数自动跑起来，最后恢复寄存器 `detach`，目标继续跑，宛如无事发生

```text
PTRACE_ATTACH attach 到进程 目标收到 SIGSTOP 暂停
PTRACE_DETACH 分离 目标继续跑
PTRACE_SEIZE 新的 attach 方式 不暂停
PTRACE_INTERRUPT 暂停被 SEIZE 的目标
PTRACE_TRACEME 子进程让父进程跟踪自己

PTRACE_CONT 继续跑
PTRACE_SYSCALL 继续跑 下次进或出系统调用时暂停
PTRACE_SINGLESTEP 单步一条指令

PTRACE_GETREGS 读通用寄存器 返回 user_regs_struct
PTRACE_SETREGS 写通用寄存器

PTRACE_PEEKDATA 读目标内存一个字 8 字节
PTRACE_POKEDATA 写目标内存一个字 8 字节
PTRACE_PEEKTEXT 读代码段 和 PEEKDATA 实际一样
PTRACE_POKETEXT 写代码段 和 POKEDATA 实际一样

注入常用组合
PTRACE_ATTACH attach
waitpid 等目标暂停
PTRACE_GETREGS 保存寄存器
PTRACE_PEEKDATA 备份原内存
PTRACE_POKEDATA 写 shellcode
PTRACE_SETREGS 改 rip
PTRACE_CONT 让它跑
PTRACE_SETREGS 恢复寄存器
PTRACE_DETACH 分离
```

`ptrace`注入的原理很简单，但是实现并不短，下列是我注入`sleep`进程的一段注入器

```c
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <elf.h>

#define LIBC_PATH  "/lib/x86_64-linux-gnu/libc.so.6"

static pid_t g_pid;
static struct user_regs_struct g_saved;

/* ---------------- 进程与符号 ---------------- */

static pid_t find_pid(const char *name)
{
    DIR *d = opendir("/proc");
    if (!d) return -1;

    struct dirent *de;
    pid_t found = -1;
    while ((de = readdir(d))) {
        if (de->d_name[0] < '0' || de->d_name[0] > '9') continue;

        char path[512], comm[256];
        snprintf(path, sizeof path, "/proc/%s/comm", de->d_name);
        FILE *f = fopen(path, "r");
        if (!f) continue;
        if (!fgets(comm, sizeof comm, f)) { fclose(f); continue; }
        fclose(f);

        comm[strcspn(comm, "\n")] = 0;
        if (strcmp(comm, name) == 0) { found = atoi(de->d_name); break; }
    }
    closedir(d);
    return found;
}

static unsigned long find_libc_base(pid_t pid)
{
    char path[64];
    snprintf(path, sizeof path, "/proc/%d/maps", pid);
    FILE *f = fopen(path, "r");
    if (!f) return 0;

    char line[512];
    unsigned long base = 0;
    while (fgets(line, sizeof line, f)) {
        unsigned long start, end, off;
        char perms[8];
        if (sscanf(line, "%lx-%lx %7s %lx", &start, &end, perms, &off) != 4)
            continue;
        if (off != 0) continue;                  
        if (!strstr(line, "libc.so.6")) continue;
        base = start;
        break;
    }
    fclose(f);
    return base;
}

static unsigned long find_function_offset(const char *libc_path, const char *function_name)
{
    FILE *f = fopen(libc_path, "rb");
    if (!f) return 0;

    Elf64_Ehdr eh;
    if (fread(&eh, sizeof eh, 1, f) != 1) { fclose(f); return 0; }

    Elf64_Shdr dynsym_sh;
    int found_dynsym = 0;
    for (int i = 0; i < eh.e_shnum; i++) {
        fseek(f, eh.e_shoff + i * sizeof(Elf64_Shdr), SEEK_SET);
        if (fread(&dynsym_sh, sizeof dynsym_sh, 1, f) != 1) break;
        if (dynsym_sh.sh_type == SHT_DYNSYM) { found_dynsym = 1; break; }
    }
    if (!found_dynsym) { fclose(f); return 0; }

    Elf64_Shdr dynstr_sh;
    fseek(f, eh.e_shoff + dynsym_sh.sh_link * sizeof(Elf64_Shdr), SEEK_SET);
    if (fread(&dynstr_sh, sizeof dynstr_sh, 1, f) != 1) { fclose(f); return 0; }

    char *dynstr = malloc(dynstr_sh.sh_size);
    Elf64_Sym *syms = malloc(dynsym_sh.sh_size);
    unsigned long result = 0;

    if (dynstr && syms) {
        fseek(f, dynstr_sh.sh_offset, SEEK_SET);
        fread(dynstr, 1, dynstr_sh.sh_size, f);
        fseek(f, dynsym_sh.sh_offset, SEEK_SET);
        size_t n = dynsym_sh.sh_size / sizeof(Elf64_Sym);
        if (fread(syms, sizeof(Elf64_Sym), n, f) == n) {
            for (size_t i = 0; i < n; i++) {
                if (syms[i].st_name >= dynstr_sh.sh_size) continue;
                if (strcmp(dynstr + syms[i].st_name, function_name) == 0) {
                    result = syms[i].st_value;
                    break;
                }
            }
        }
    }
    free(dynstr);
    free(syms);
    fclose(f);
    return result;
}

/* ---------------- ptrace ---------------- */

static int poke(unsigned long addr, const void *buf, size_t len)
{
    for (size_t i = 0; i < len; i += 8) {
        long word = 0;
        size_t n = (len - i < 8) ? (len - i) : 8;
        memcpy(&word, (const char *)buf + i, n);
        if (ptrace(PTRACE_POKEDATA, g_pid, (void *)(addr + i),
                   (void *)(uintptr_t)word) < 0) {
            fprintf(stderr, "POKEDATA 0x%lx: %s\n", addr + i, strerror(errno));
            return -1;
        }
    }
    return 0;
}

/*
 * 在目标进程里调一个 libc 函数。
 *
 * rsp 要摆成 16n+8：x86-64 的 ABI 规定函数入口处 rsp % 16 == 8，
 * 也就是 call 压完返回地址之后的样子。这里用 ret 返回，栈顶放 0，
 * 函数 ret 时跳到 0 触发 SIGSEGV
 *
 * orig_rax 必须清掉：目标多半正卡在某个系统调用里（比如 sleep 的
 * clock_nanosleep），内核在 syscall 退出路径上会把 rip 回退 2 字节
 * （syscall 指令的长度）不清的话，明明设的是函数入口，实际会跑到
 * 入口前两个字节，撞上填充字节直接崩
 */
static int call_remote(unsigned long fn,
                       unsigned long a1, unsigned long a2, unsigned long a3,
                       unsigned long a4, unsigned long a5, unsigned long a6,
                       unsigned long *ret)
{
    struct user_regs_struct r = g_saved;
    long zero = 0;
    int status;

    unsigned long sp = ((g_saved.rsp - 0x800) & ~0xFUL) - 8;

    if (poke(sp, &zero, sizeof zero) < 0) return -1;

    r.rdi = a1; r.rsi = a2; r.rdx = a3;
    r.rcx = a4; r.r8  = a5; r.r9  = a6;
    r.orig_rax = (unsigned long)-1;
    r.rip = fn;
    r.rsp = sp;

    if (ptrace(PTRACE_SETREGS, g_pid, NULL, &r) < 0) {
        fprintf(stderr, "SETREGS: %s\n", strerror(errno));
        return -1;
    }
    if (ptrace(PTRACE_CONT, g_pid, NULL, NULL) < 0) {
        fprintf(stderr, "CONT: %s\n", strerror(errno));
        return -1;
    }
    if (waitpid(g_pid, &status, 0) < 0) {
        fprintf(stderr, "waitpid: %s\n", strerror(errno));
        return -1;
    }
    if (!WIFSTOPPED(status)) {
        fprintf(stderr, "target died\n");
        return -1;
    }

    struct user_regs_struct out;
    if (ptrace(PTRACE_GETREGS, g_pid, NULL, &out) < 0) {
        fprintf(stderr, "GETREGS: %s\n", strerror(errno));
        return -1;
    }

    *ret = out.rax;
    return 0;
}

/* ---------------- main ---------------- */

int main(int argc, char *argv[])
{
    if (argc < 3) {
        printf("usage: %s <process-name> <path-to-so>\n", argv[0]);
        return 1;
    }

    printf("Finding PID of process...\n");
    char *name = argv[1];
    pid_t pid = find_pid(name);
    if (pid == -1) { printf("Process not found.\n"); return 1; }
    printf("PID of process '%s' is %d\n", name, pid);

    g_pid = pid;

    unsigned long libc_base = find_libc_base(pid);
    if (libc_base == 0) { printf("Failed to find libc base.\n"); return 1; }
    printf("Base address of libc in process '%s' is 0x%lx\n", name, libc_base);

    unsigned long dlopen_offset = find_function_offset(LIBC_PATH, "dlopen");
    if (dlopen_offset == 0) { printf("Failed to find dlopen offset.\n"); return 1; }
    printf("Offset of dlopen in libc is 0x%lx\n", dlopen_offset);

    unsigned long dlopen_addr = libc_base + dlopen_offset;

    ptrace(PTRACE_ATTACH, pid, NULL, NULL);
    waitpid(pid, NULL, 0);

    struct user_regs_struct old_regs;
    ptrace(PTRACE_GETREGS, pid, NULL, &old_regs);
    g_saved = old_regs;

    /* so 路径直接写在目标进程的栈上，这样整个注入只发一次远程调用 */
    const char *so_path = argv[2];
    unsigned long str_addr = (old_regs.rsp - 0x1000) & ~0xFUL;
    poke(str_addr, so_path, strlen(so_path) + 1);

    unsigned long handle = 0;
    call_remote(dlopen_addr, str_addr, 2, 0, 0, 0, 0, &handle);
    printf("dlopen handle = 0x%lx\n", handle);

    /* 恢复寄存器，放目标继续跑 */
    ptrace(PTRACE_SETREGS, pid, NULL, &old_regs);
    ptrace(PTRACE_CONT, pid, NULL, NULL);
    ptrace(PTRACE_DETACH, pid, NULL, NULL);

    return 0;
}
```

`hook.c`如下

```c
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>

__attribute__((constructor)) void my_init(void) {
    // 写文件证明加载了
    FILE *f = fopen("/tmp/hook_loaded.txt", "w");
    if (f) {
        fprintf(f, "hook loaded pid=%d\n", getpid());
        fclose(f);
    }

    // 直接用 syscall write 到 stderr 避免依赖 stdio 状态
    const char msg[] = "[hook] injected\n";
    syscall(SYS_write, 2, msg, sizeof(msg) - 1);
}
```

也就是真正做到了`「在一个正在运行的进程里加载任意 .so，并让它的代码真正跑起来」`

哦不过注意一下，你要`ptrace`非子进程记得`root`一下，不然会失败
