# Drink_some_tea WriteUp

（一道超级好题，学到好多东西，花了大概两三天时间，感谢tony老师哦）

知识点（花指令，seh,tea）

这题一打开就是花指令

我尽可能详细写出去花过程

第一处:

```
.text:004012F1 53                                push    ebx
.text:004012F2 33 DB                             xor     ebx, ebx
.text:004012F4 85 DB                             test    ebx, ebx
.text:004012F6 75 02                             jnz     short loc_4012FA
.text:004012F6
.text:004012F8 74 01                             jz      short near ptr loc_4012FA+1
.text:004012F8
.text:004012FA
.text:004012FA                                   loc_4012FA:                             ; CODE XREF: .text:004012F6↑j
.text:004012FA                                                                         ; .text:004012F8↑j
.text:004012FA 39 5B C7                          cmp     [ebx-39h], ebx
.text:004012FD 45                                inc     ebp
.text:004012FE EC                                in      al, dx
.text:004012FF 14 45                             adc     al, 45h ; 'E'
.text:00401301 11 00                             adc     [eax], eax
.text:00401303 C7 45 F0 10 98 91 01              mov     dword ptr [ebp-10h], 1919810h
.text:0040130A C7 45 F4 BB C5 39 00              mov     dword ptr [ebp-0Ch], 39C5BBh
.text:00401311 C7 45 F8 11 E2 FF 00              mov     dword ptr [ebp-8], 0FFE211h

.text:004012F1 53                                push    ebx首先这个是把目前的信息保存到栈顶，所以推测pop ebx 将会是花指令结束点

.text:004012F2 33 DB                             xor     ebx, ebx
.text:004012F4 85 DB                             test    ebx, ebx

.text:004012F8 74 01                             jz      short near ptr loc_4012FA+1
```

ebx xor自己就等于赋值0 于是jz在test作用下必然执行

这一个jump 我们发现跳到指令中间了

```
.text:004012FA 39 5B C7                          cmp     [ebx-39h], ebx
```

也就是这个39一定不会执行的 直接nop掉啦

```
.text:004012F1 53                                push    ebx
.text:004012F2 33 DB                             xor     ebx, ebx
.text:004012F4 85 DB                             test    ebx, ebx
.text:004012F6 75 02                             jnz     short loc_4012FA
.text:004012F6
.text:004012F8 74 01                             jz      short loc_4012FB
.text:004012F8
.text:004012FA
.text:004012FA                                   loc_4012FA:                             ; CODE XREF: .text:004012F6↑j
.text:004012FA 90                                nop
.text:004012FA
.text:004012FB
.text:004012FB                                   loc_4012FB:                             ; CODE XREF: .text:004012F8↑j
.text:004012FB 5B                                pop     ebx
.text:004012FB
.text:004012FB                                   ; ---------------------------------------------------------------------------
.text:004012FC C7                                db 0C7h
.text:004012FD                                   ; ---------------------------------------------------------------------------
.text:004012FD 45                                inc     ebp
.text:004012FE EC                                in      al, dx
.text:004012FF 14 45                             adc     al, 45h ; 'E'
.text:00401301 11 00                             adc     [eax], eax
.text:00401303 C7 45 F0 10 98 91 01              mov     dword ptr [ebp-10h], 1919810h
.text:0040130A C7 45 F4 BB C5 39 00              mov     dword ptr [ebp-0Ch], 39C5BBh
.text:00401311 C7 45 F8 11 E2 FF 00              mov     dword ptr [ebp-8], 0FFE211h
.text:00401318 33 C0                             xor     eax, eax
```

nop完成这样 我们才推测完pop ebx 是结束点 故

```
.text:004012FB
.text:004012FB                                   ; ---------------------------------------------------------------------------
.text:004012FC C7                                db 0C7h
.text:004012FD                                   ; ---------------------------------------------------------------------------
.text:004012FD 45                                inc     ebp
.text:004012FE EC                                in      al, dx
.text:004012FF 14 45                             adc     al, 45h ; 'E'
.text:00401301 11 00                             adc     [eax], eax
.text:00401303 C7 45 F0 10 98 91 01              mov     dword ptr [ebp-10h], 1919810h
.text:0040130A C7 45 F4 BB C5 39 00              mov     dword ptr [ebp-0Ch], 39C5BBh
.text:00401311 C7 45 F8 11 E2 FF 00              mov     dword ptr [ebp-8], 0FFE211h
.text:00401318 33 C0                             xor     eax, eax
```

都应该是正常指令

所以我们应该在

```
.text:004012FD 45                                inc     ebp
```

按住U (Undefined)

并在 

```
.text:004012FB                                   loc_4012FB:
```

按C重新识别 

得到

```
.text:004012FB                                   loc_4012FB:                             ; CODE XREF: .text:004012F8↑j
.text:004012FB 5B                                pop     ebx
.text:004012FC C7 45 EC 14 45 11 00              mov     dword ptr [ebp-14h], 114514h
.text:00401303 C7 45 F0 10 98 91 01              mov     dword ptr [ebp-10h], 1919810h
.text:0040130A C7 45 F4 BB C5 39 00              mov     dword ptr [ebp-0Ch], 39C5BBh
.text:00401311 C7 45 F8 11 E2 FF 00              mov     dword ptr [ebp-8], 0FFE211h
.text:00401318 33 C0                             xor     eax, eax
.text:0040131A 85 C0                             test    eax, eax
```

但是紧接着第二处

```
.text:00401318 33 C0                             xor     eax, eax
.text:0040131A 85 C0                             test    eax, eax
.text:0040131C 74 0B                             jz      short near ptr locret_401328+1
.text:0040131C
.text:0040131E 75 00                             jnz     short $+2
.text:0040131E
.text:00401320
.text:00401320                                   loc_401320:                             ; CODE XREF: .text:0040131E↑j
.text:00401320 5E                                pop     esi
.text:00401321 23 C3                             and     eax, ebx
.text:00401323 50                                push    eax
.text:00401324 33 C3                             xor     eax, ebx
.text:00401326 74 03                             jz      short loc_40132B
.text:00401326
.text:00401328
.text:00401328                                   locret_401328:                          ; CODE XREF: .text:0040131C↑j
.text:00401328 C2 8D 4D                          retn    4D8Dh
.text:00401328
.text:0040132B                                   ; ---------------------------------------------------------------------------
.text:0040132B
.text:0040132B                                   loc_40132B:                             ; CODE XREF: .text:00401326↑j
.text:0040132B E0 51                             loopne  near ptr loc_40137C+2
```

首先我们知道jz一定跳 而且跳到8D

```
.text:00401328 C2 8D 4D                          retn    4D8Dh 
```

于是nop C2 

得到

```
.text:0040131A 85 C0                             test    eax, eax
.text:0040131C 74 0B                             jz      short near ptr unk_401329
.text:0040131C
.text:0040131E 75 00                             jnz     short $+2
.text:0040131E
.text:00401320
.text:00401320                                   loc_401320:                             ; CODE XREF: .text:0040131E↑j
.text:00401320 5E                                pop     esi
.text:00401321 23 C3                             and     eax, ebx
.text:00401323 50                                push    eax
.text:00401324 33 C3                             xor     eax, ebx
.text:00401326 74 03                             jz      short loc_40132B
.text:00401326
.text:00401328 90                                nop
.text:00401328
.text:00401328                                   ; ---------------------------------------------------------------------------
.text:00401329 8D                                unk_401329 db  8Dh                      ; CODE XREF: .text:0040131C↑j
.text:0040132A 4D                                db  4Dh ; M
.text:0040132B                                   ; ---------------------------------------------------------------------------
.text:0040132B
.text:0040132B                                   loc_40132B:                             ; CODE XREF: .text:00401326↑j
.text:0040132B E0 51                             loopne  near ptr loc_40137C+2
```

很容易知道中间啥的都不执行啊

全nop算了 ：）

```
text:00401318 33 C0                             xor     eax, eax
.text:0040131A 85 C0                             test    eax, eax
.text:0040131C 74 0B                             jz      short near ptr unk_401329
.text:0040131C
.text:0040131E                                   ; ; patched 0xb
.text:0040131E 90                                nop
.text:0040131F 90                                nop
.text:00401320 90                                nop
.text:00401321 90                                nop
.text:00401322 90                                nop
.text:00401323 90                                nop
.text:00401324 90                                nop
.text:00401325 90                                nop
.text:00401326 90                                nop
.text:00401327 90                                nop
.text:00401328 90                                nop
.text:00401328
.text:00401328                                   ; ---------------------------------------------------------------------------
.text:00401329 8D                                unk_401329 db  8Dh                      ; CODE XREF: .text:0040131C↑j
.text:0040132A 4D                                db  4Dh ; M
.text:0040132B                                   ; ---------------------------------------------------------------------------
.text:0040132B E0 51                             loopne  near ptr loc_40137C+2
.text:0040132B
.text:0040132D 8D 55 EC                          lea     edx, [ebp-14h]
.text:00401330 52                                push    edx
.text:00401331 8B 45 E8                          mov     eax, [ebp-18h]
.text:00401334 50                                push    eax
.text:00401335 E8 96 FE FF FF                    call    sub_4011D0
```

那我们看到人家是跳到

```
.text:00401329 8D                                unk_401329 db  8Dh                      ; CODE XREF: .text:0040131C↑j
```

这一条 

所以后面都是有用的，直接在

```
.text:0040132B E0 51                             loopne  near ptr loc_40137C+2 
```

按U 再去函数头按C就行

得到

```
.text:004012FB                                   loc_4012FB:                             ; CODE XREF: _main+38↑j
.text:004012FB 034 5B                            pop     ebx
.text:004012FC 030 C7 45 EC 14 45 11 00          mov     [ebp+var_14], 114514h
.text:00401303 030 C7 45 F0 10 98 91 01          mov     [ebp+var_10], 1919810h
.text:0040130A 030 C7 45 F4 BB C5 39 00          mov     [ebp+var_C], 39C5BBh
.text:00401311 030 C7 45 F8 11 E2 FF 00          mov     [ebp+var_8], 0FFE211h
.text:00401318 030 33 C0                         xor     eax, eax
.text:0040131A 030 85 C0                         test    eax, eax
.text:0040131C 030 74 0B                         jz      short loc_401329
.text:0040131C
.text:0040131E                                   ; ; patched 0xb
.text:0040131E 030 90                            nop
.text:0040131F 030 90                            nop
.text:00401320 030 90                            nop
.text:00401321 030 90                            nop
.text:00401322 030 90                            nop
.text:00401323 030 90                            nop
.text:00401324 030 90                            nop
.text:00401325 030 90                            nop
.text:00401326 030 90                            nop
.text:00401327 030 90                            nop
.text:00401328 030 90                            nop
.text:00401328
.text:00401329
.text:00401329                                   loc_401329:                             ; CODE XREF: _main+5C↑j
.text:00401329 030 8D 4D E0                      lea     ecx, [ebp+var_20]
.text:0040132C 030 51                            push    ecx                             ; int
.text:0040132D 034 8D 55 EC                      lea     edx, [ebp+var_14]
.text:00401330 034 52                            push    edx                             ; int
.text:00401331 038 8B 45 E8                      mov     eax, [ebp+Src]
.text:00401334 038 50                            push    eax                             ; Src
.text:00401335 03C E8 96 FE FF FF                call    sub_4011D0
.text:00401335
```

这两处就去完了

往下翻了一会没看到了

shift+f12找找 

翻到个correct,那不得看看

得到

```
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v4; // [esp+Ch] [ebp-20h] BYREF
  void *Block; // [esp+10h] [ebp-1Ch]
  void *Src; // [esp+14h] [ebp-18h]
  int v7[4]; // [esp+18h] [ebp-14h] BYREF

  Src = malloc(0x64u);
  sub_401460(&unk_422030, (char)Src);
  v7[0] = 1131796;
  v7[1] = 26318864;
  v7[2] = 3786171;
  v7[3] = 16769553;
  Block = (void *)sub_4011D0(Src, (int)v7, (int)&v4);
  if ( sub_40211E(Block, &unk_422000, 48) )
    sub_401420(Wrong_n);                        // "Wrong\n"
  else
    sub_401420(aCorrect);                       // "Correct\n"
  free(Block);
  return 0;
}
```

好丑我改个名

```
int __cdecl main(int argc, const char **argv, const char **envp)
{
  int v4; // [esp+Ch] [ebp-20h] BYREF
  void *Block; // [esp+10h] [ebp-1Ch]
  void *input; // [esp+14h] [ebp-18h]
  int v7[4]; // [esp+18h] [ebp-14h] BYREF

  input = malloc(0x64u);
  scanf(&unk_422030, (char)input);
  v7[0] = 1131796;
  v7[1] = 26318864;
  v7[2] = 3786171;
  v7[3] = 16769553;
  Block = (void *)encry(input, (int)v7, (int)&v4);
  if ( check(Block, &unk_422000, 48) )
    printf(Wrong_n);                            // "Wrong\n"
  else
    printf(aCorrect);                           // "Correct\n"
  free(Block);
  return 0;
}
```

追到encry里面看看

```
void *__cdecl encry(const char *Src, int a2, _DWORD *a3)
{
  void *result; // eax
  void *v4; // [esp+14h] [ebp-14h]
  size_t Size; // [esp+18h] [ebp-10h]
  void *Block; // [esp+1Ch] [ebp-Ch]
  unsigned int Count; // [esp+20h] [ebp-8h]

  Size = strlen(Src);
  Count = 8 * ((Size + 7) >> 3);
  Block = calloc(Count, 1u);
  memmove(Block, Src, Size);
  result = malloc(Count);
  v4 = result;
  if ( !Count )
  {
    free(Block);
    *a3 = 0;
    return v4;
  }
  return result;
}
```

我一开始看到这个没看到加密逻辑在哪，人都不好了TT 

以后遇到这种逻辑看不到的可以试试看看汇编有无花

按Tab 进反汇编视角

```
ext:0040123D                                   loc_40123D:                             ; CODE XREF: encry+62↑j
.text:0040123D 02C 8B 55 FC                      mov     edx, [ebp+var_4]
.text:00401240 02C 3B 55 F8                      cmp     edx, [ebp+Count]
.text:00401243 02C 73 4F                         jnb     short loc_401294
.text:00401243
.text:00401245 02C E8 01 00 00 00                call    loc_40124B
.text:00401245
.text:00401245                                   ; ---------------------------------------------------------------------------
.text:0040124A 02C 83                            db 83h
.text:0040124B                                   ; ---------------------------------------------------------------------------
.text:0040124B
.text:0040124B                                   loc_40124B:                             ; CODE XREF: encry+75↑j
.text:0040124B                                   db      36h
.text:0040124B 02C 36 83 04 24 08                add     [esp+28h+var_28], 8
.text:00401250 02C C3                            retn
.text:00401250
.text:00401250                                   ; ---------------------------------------------------------------------------
.text:00401251 02C F3 6A 08                      db 0F3h, 6Ah, 8                         ; Size
.text:00401254                                   ; ---------------------------------------------------------------------------
.text:00401254 030 8B 45 F4                      mov     eax, [ebp+Block]
.text:00401257 030 03 45 FC                      add     eax, [ebp+var_4]
.text:0040125A 030 50                            push    eax             
```

果然！

第三处的花指令需要我们好好分析一下

首先我们的cpu是要到哪里呢

call指令是会把下一条地址压栈

这里就是压入0040124A

但是83h不被执行，因为跳到了

```
.text:0040124B                                   loc_40124B:                             ; CODE XREF: encry+75↑j
.text:0040124B                                   db      36h
.text:0040124B 02C 36 83 04 24 08                add     [esp+28h+var_28], 8
.text:00401250 02C C3                            retn
```

这个东西在干什么？

db不管他没用的

```
.text:0040124B 02C 36 83 04 24 08                add     [esp+28h+var_28], 8
```

这个是给esp加了8！

但栈顶本来是0040124A，加八直接变成00401252

然后retn是pop+jump 于是跳到了00401252

好分析完我们知道，其实做了这么多就是直接跳到了00401252

那就很简单了 全nop掉就行

```
.text:00401251 02C F3 6A 08                      db 0F3h, 6Ah, 8                         ; Size
```

先看52是在6A 先把F3 nop了 额我个人比较喜欢按U拆开好看

```
text:0040123D 02C 8B 55 FC                      mov     edx, [ebp+var_4]
.text:00401240 02C 3B 55 F8                      cmp     edx, [ebp+Count]
.text:00401243 02C 73 4F                         jnb     short loc_401294
.text:00401243
.text:00401245 02C E8 01 00 00 00                call    loc_40124B
.text:00401245
.text:00401245                                   ; ---------------------------------------------------------------------------
.text:0040124A 02C 83                            db 83h
.text:0040124B                                   ; ---------------------------------------------------------------------------
.text:0040124B
.text:0040124B                                   loc_40124B:                             ; CODE XREF: encry+75↑j
.text:0040124B                                   db      36h
.text:0040124B 02C 36 83 04 24 08                add     [esp+28h+var_28], 8
.text:00401250 02C C3                            retn
.text:00401250
.text:00401250                                   ; ---------------------------------------------------------------------------
.text:00401251 02C 90                            db  90h                                 ; Size
.text:00401252 02C 6A                            db  6Ah ; j
.text:00401253 02C 08                            db    8
.text:00401254                                   ; ---------------------------------------------------------------------------
.text:00401254 030 8B 45 F4                      mov     eax, [ebp+Block]
.text:00401257 030 03 45 FC                      add     eax, [ebp+var_4]
.text:0040125A 030 50                            push    eax                             ; Src
.text:0040125B 034 8D 4D E4                      lea     ecx, [ebp+var_1C]
.text:0040125E 034 51                            push    ecx                             ; void *
.text:0040125F 038 E8 4C 25 00 00                call    _memmove
.text:0040125F
```

全nop即可 再UC 重组得到

```
.text:0040123D 02C 8B 55 FC                      mov     edx, [ebp+var_4]
.text:00401240 02C 3B 55 F8                      cmp     edx, [ebp+Count]
.text:00401243                                   ; ; patched 0xe
.text:00401243 02C 90                            nop
.text:00401244 02C 90                            nop
.text:00401245 02C 90                            nop
.text:00401246 02C 90                            nop
.text:00401247 02C 90                            nop
.text:00401248 02C 90                            nop
.text:00401249 02C 90                            nop
.text:0040124A 02C 90                            nop
.text:0040124B 02C 90                            nop
.text:0040124C 02C 90                            nop
.text:0040124D 02C 90                            nop
.text:0040124E 02C 90                            nop
.text:0040124F 02C 90                            nop
.text:00401250 02C 90                            nop
.text:00401251 02C 90                            nop                                     ; Size
.text:00401252 02C 6A 08                         push    8                               ; Size
.text:00401254 030 8B 45 F4                      mov     eax, [ebp+Block]
.text:00401257 030 03 45 FC                      add     eax, [ebp+var_4]
.text:0040125A 030 50                            push    eax                             ; Src
.text:0040125B 034 8D 4D E4                      lea     ecx, [ebp+var_1C]
.text:0040125E 034 51                            push    ecx                             ; void *
.text:0040125F 038 E8 4C 25 00 00                call    _memmove
```

回去看看

```
void __cdecl __noreturn encry(const char *Src)
{
  _BYTE v1[8]; // [esp+Ch] [ebp-1Ch] BYREF
  char *v2; // [esp+14h] [ebp-14h]
  size_t Size; // [esp+18h] [ebp-10h]
  void *Block; // [esp+1Ch] [ebp-Ch]
  size_t Count; // [esp+20h] [ebp-8h]
  unsigned int i; // [esp+24h] [ebp-4h]

  Size = strlen(Src);
  Count = 8 * ((Size + 7) >> 3);
  Block = calloc(Count, 1u);
  memmove(Block, Src, Size);
  v2 = (char *)malloc(Count);
  for ( i = 0; ; i += 8 )
  {
    memmove(v1, (char *)Block + i, 8u);
    __scrt_common_main_seh();
    memmove(&v2[4 * (i >> 2)], v1, 8u);
  }
}
```

嗯果然啊

试试点__scrt_common_main_seh()

依旧有花（神了也是）

```
.text:004010AE 058 50                            push    eax
.text:004010AF 05C 33 C0                         xor     eax, eax
.text:004010B1 05C 85 C0                         test    eax, eax
.text:004010B3 05C 75 02                         jnz     short loc_4010B7
.text:004010B3
.text:004010B5 05C 74 01                         jz      short near ptr loc_4010B7+1
.text:004010B5
.text:004010B7
.text:004010B7                                   loc_4010B7:                             ; CODE XREF: __scrt_common_main_seh(void)+B3↑j
.text:004010B7                                                                           ; __scrt_common_main_seh(void)+B5↑j
.text:004010B7 05C E8 C6 45 D4 00                call    near ptr 1145682h
.text:004010B7
.text:004010BC 05C E8 01 00 00 00                call    loc_4010C2
.text:004010BC
.text:004010BC                                   ?__scrt_common_main_seh@@YAHXZ endp ; sp-analysis failed
.text:004010BC
.text:004010BC                                   ; ---------------------------------------------------------------------------
.text:004010C1 FF                                db 0FFh
.text:004010C2                                   ; ---------------------------------------------------------------------------
.text:004010C2                                   ; START OF FUNCTION CHUNK FOR __scrt_common_main_seh(void)
.text:004010C2
.text:004010C2                                   loc_4010C2:                             ; CODE XREF: __scrt_common_main_seh(void)+BC↑j
.text:004010C2                                   db      36h
.text:004010C2 05C 36 83 04 24 08                add     [esp+58h+var_58], 8
.text:004010C7 05C C3                            retn
.text:004010C7
.text:004010C7                                   ; END OF FUNCTION CHUNK FOR __scrt_common_main_seh(void)
.text:004010C8                                   ; ---------------------------------------------------------------------------
.text:004010C8 11 C6                             adc     esi, eax
.text:004010CA 45                                inc     ebp
.text:004010CB D4 02                             aam     2
.text:004010CD 58                                pop     eax
```

首先起点终点确定

```
.text:004010AE 058 50                            push    eax

.text:004010CD 58                                pop     eax
```

其实这里有两处

第一处是一个强跳

```
.text:004010AE 058 50                            push    eax
.text:004010AF 05C 33 C0                         xor     eax, eax
.text:004010B1 05C 85 C0                         test    eax, eax
.text:004010B3 05C 75 02                         jnz     short loc_4010B7
.text:004010B3
.text:004010B5 05C 74 01                         jz      short near ptr loc_4010B7+1
.text:004010B5
.text:004010B7
.text:004010B7                                   loc_4010B7:                             ; CODE XREF: __scrt_common_main_seh(void)+B3↑j
.text:004010B7                                                                           ; __scrt_common_main_seh(void)+B5↑j
.text:004010B7 05C E8 C6 45 D4 00                call    near ptr 1145682h
```

跳到loc_4010B8

那就nop E8得到

```
.text:004010AE 058 50                            push    eax
.text:004010AF 05C 33 C0                         xor     eax, eax
.text:004010B1 05C 85 C0                         test    eax, eax
.text:004010B3 05C 75 02                         jnz     short loc_4010B7
.text:004010B3
.text:004010B5 05C 74 01                         jz      short loc_4010B8
.text:004010B5
.text:004010B7
.text:004010B7                                   loc_4010B7:                             ; CODE XREF: __scrt_common_main_seh(void)+B3↑j
.text:004010B7 05C 90                            nop
.text:004010B7
.text:004010B8
.text:004010B8                                   loc_4010B8:                             ; CODE XREF: __scrt_common_main_seh(void)+B5↑j
.text:004010B8 05C C6 45 D4 00                   mov     byte ptr [ebp+var_2C], 0
.text:004010BC 05C E8 01 00 00 00                call    loc_4010C2
.text:004010BC
.text:004010BC                                   ?__scrt_common_main_seh@@YAHXZ endp ; sp-analysis failed
.text:004010BC
.text:004010BC                                   ; ---------------------------------------------------------------------------
.text:004010C1 FF                                db 0FFh
.text:004010C2                                   ; ---------------------------------------------------------------------------
.text:004010C2                                   ; START OF FUNCTION CHUNK FOR __scrt_common_main_seh(void)
.text:004010C2
.text:004010C2                                   loc_4010C2:                             ; CODE XREF: __scrt_common_main_seh(void)+BC↑j
.text:004010C2                                   db      36h
.text:004010C2 05C 36 83 04 24 08                add     [esp+58h+var_58], 8
.text:004010C7 05C C3                            retn
.text:004010C7
.text:004010C7                                   ; END OF FUNCTION CHUNK FOR __scrt_common_main_seh(void)
.text:004010C8                                   ; ---------------------------------------------------------------------------
.text:004010C8 11 C6                             adc     esi, eax
.text:004010CA 45                                inc     ebp
.text:004010CB D4 02                             aam     2
.text:004010CD 58                                pop     eax
```

同上分析得到跳到C9了

```
.text:004010AE 058 50                            push    eax
.text:004010AF 05C 33 C0                         xor     eax, eax
.text:004010B1 05C 85 C0                         test    eax, eax
.text:004010B3 05C 75 02                         jnz     short loc_4010B7
.text:004010B3
.text:004010B5                                   ; ; patched 0x13
.text:004010B5 05C 90                            nop
.text:004010B6 05C 90                            nop
.text:004010B6
.text:004010B7
.text:004010B7                                   loc_4010B7:                             ; CODE XREF: __scrt_common_main_seh(void)+B3↑j
.text:004010B7 05C 90                            nop
.text:004010B8 05C 90                            nop
.text:004010B9 05C 90                            nop
.text:004010BA 05C 90                            nop
.text:004010BB 05C 90                            nop
.text:004010BB                                   ?__scrt_common_main_seh@@YAHXZ endp ; sp-analysis failed
.text:004010BB
.text:004010BC 90                                nop
.text:004010BD 90                                nop
.text:004010BE 90                                nop
.text:004010BF 90                                nop
.text:004010C0 90                                nop
.text:004010C1 90                                nop
.text:004010C2 90                                nop
.text:004010C3 90                                nop
.text:004010C4 90                                nop
.text:004010C5 90                                nop
.text:004010C6 90                                nop
.text:004010C7 90                                nop
.text:004010C8 90                                nop
.text:004010C9 C6 45 D4 02                       mov     byte ptr [ebp-2Ch], 2
.text:004010CD 58                                pop     eax
```

全nop得到这个 然后去到这个函数整个函数头

```
.text:00401000                                   ?__scrt_common_main_seh@@YAHXZ proc near
```

 U P 一下就行 

哎有人就要说了哎呀为什么这里是P？

这是因为

```
.text:004010BB                                   ?__scrt_common_main_seh@@YAHXZ endp ; sp-analysis failed
```

这个问题，局部按C没用了 需要重新分析这整个函数 P

得到

```
unsigned int __cdecl __scrt_common_main_seh(unsigned int *a1, int a2)
{
  int i; // [esp+2Ch] [ebp-28h]
  unsigned int v4; // [esp+30h] [ebp-24h]
  unsigned int v5; // [esp+34h] [ebp-20h]
  unsigned int v6; // [esp+38h] [ebp-1Ch]

  v5 = *a1;
  v4 = a1[1];
  v6 = 0;
  for ( i = 0; i < 32; ++i )
  {
    v5 += (*(_DWORD *)(a2 + 4 * (v6 & 3)) + v6) ^ (v4 + ((v4 >> 5) ^ (16 * v4)));
    if ( !v6 )
      MEMORY[0] = 0;
    v6 -= 1640531527;
    v4 += (*(_DWORD *)(a2 + 4 * ((v6 >> 11) & 3)) + v6) ^ (v5 + ((v5 >> 5) ^ (16 * v5)));
  }
  *a1 = v5;
  a1[1] = v4;
  return v4;
}
```

至此花指令去完了（其实我本来以为这个也是花，但我看半天没找着）

但是我们看到！

```
text:00401000 000 55                            push    ebp
.text:00401001 004 8B EC                         mov     ebp, esp
.text:00401003 004 6A FE                         push    0FFFFFFFEh
.text:00401005 008 68 E0 0F 42 00                push    offset stru_420FE0
.text:0040100A 00C 68 70 3D 40 00                push    offset SEH_41A090
.text:0040100F 010 64 A1 00 00 00 00             mov     eax, large fs:0
.text:00401015 010 50                            push    eax
.text:00401016 014 83 C4 CC                      add     esp, 0FFFFFFCCh
.text:00401019 048 53                            push    ebx
.text:0040101A 04C 56                            push    esi
```

有SEH标签啊(https://bbs.kanxue.com/thread-249592-1.htm)(有一位高手是用的动调，我这里纯静态分析)

于是下找try模块

```
.text:004010CE 058 C7 45 FC 00 00 00 00          mov     [ebp+ms_exc.registration.TryLevel], 0
```

找到这个

发现赋值0

回到开头追踪结构体

```
.text:00401005 008 68 E0 0F 42 00                push    offset stru_420FE0
```

点进去看第一个

```
.rdata:00420FE0 FE FF FF FF 00 00 00 00 AC FF     stru_420FE0 _EH4_SCOPETABLE <0FFFFFFFEh, 0, 0FFFFFFACh, 0, <0FFFFFFFEh, \
.rdata:00420FE0 FF FF 00 00 00 00 FE FF FF FF                                             ; DATA XREF: __scrt_common_main_seh(void)+5↑o
.rdata:00420FE0 09 11 40 00 19 11 40 00                            offset loc_401109, offset loc_401119>>
```

额offset loc_401119

追过去看看（disass页面按G输入地址）

```
.text:00401119                                   loc_401119:                             ; DATA XREF: .rdata:stru_420FE0↓o
.text:00401119 058 8B 65 E8                      mov     esp, [ebp+ms_exc.old_esp]
.text:0040111C 058 8B 55 C4                      mov     edx, [ebp+var_3C]
.text:0040111F 058 89 55 D0                      mov     [ebp+var_30], edx
.text:00401122 058 81 7D D0 05 00 00 C0          cmp     [ebp+var_30], 0C0000005h
.text:00401129 058 75 0F                         jnz     short loc_40113A
.text:00401129
.text:0040112B 058 68 E8 07 00 00                push    7E8h                            ; Seed
.text:00401130 05C E8 C8 B4 00 00                call    _srand
.text:00401130
.text:00401135 05C 83 C4 04                      add     esp, 4
.text:00401138 058 EB 14                         jmp     short loc_40114E
.text:00401138
.text:0040113A                                   ; ---------------------------------------------------------------------------
.text:0040113A
.text:0040113A                                   loc_40113A:                             ; CODE XREF: __scrt_common_main_seh(void)+129↑j
.text:0040113A 058 81 7D D0 94 00 00 C0          cmp     [ebp+var_30], 0C0000094h
.text:00401141 058 75 0B                         jnz     short loc_40114E
.text:00401141
.text:00401143 058 E8 94 B4 00 00                call    _rand
.text:00401143
.text:00401148 058 03 45 E4                      add     eax, [ebp+var_1C]
.text:0040114B 058 89 45 E4                      mov     [ebp+var_1C], eax

.text:00401122 058 81 7D D0 05 00 00 C0          cmp     [ebp+var_30], 0C0000005h

.text:0040113A 058 81 7D D0 94 00 00 C0          cmp     [ebp+var_30], 0C0000094h
```

上网查查异常号呗

0C0000005h
这个错误代码本质上是系统发出的 “ 内存访问异常 警报”（百度的）
0C0000094h
在程序运行过程中，出现0xC0000094错误通常是因为发生了整数除以零的操作。这是操作系统或处理器对非法算术操作的响应

找找发生位置

```
.text:004010DB 058 C7 45 CC 00 00 00 00          mov     [ebp+var_34], 0
.text:004010E2 058 8B 4D CC                      mov     ecx, [ebp+var_34]
.text:004010E5 058 C7 01 00 00 00 00             mov     dword ptr [ecx], 0
.text:004010EB 058 EB 13                         jmp     short loc_401100
.text:004010EB
.text:004010ED                                   ; ---------------------------------------------------------------------------
.text:004010ED
.text:004010ED                                   loc_4010ED:                             ; CODE XREF: __scrt_common_main_seh(void)+D9↑j
.text:004010ED 058 C7 45 C8 00 00 00 00          mov     [ebp+var_38], 0
.text:004010F4 058 B8 01 00 00 00                mov     eax, 1
.text:004010F9 058 99                            cdq
.text:004010FA 058 F7 7D C8                      idiv    [ebp+var_38]
.text:004010FD 058 89 45 BC                      mov     [ebp+var_44], eax
```


看到这两
```
.text:004010E5 058 C7 01 00 00 00 00             mov     dword ptr [ecx], 0
.text:004010FA 058 F7 7D C8                      idiv    [ebp+var_38]
```

然后看看ebp+var_38这是v6

unsigned int v6; // [esp+38h] [ebp-1Ch]

分析下逻辑

```
.text:00401119                                   loc_401119:                             ; DATA XREF: .rdata:stru_420FE0↓o
.text:00401119 058 8B 65 E8                      mov     esp, [ebp+ms_exc.old_esp]
.text:0040111C 058 8B 55 C4                      mov     edx, [ebp+var_3C]
.text:0040111F 058 89 55 D0                      mov     [ebp+var_30], edx
.text:00401122 058 81 7D D0 05 00 00 C0          cmp     [ebp+var_30], 0C0000005h
.text:00401129 058 75 0F                         jnz     short loc_40113A
.text:00401129
.text:0040112B 058 68 E8 07 00 00                push    7E8h                            ; Seed
.text:00401130 05C E8 C8 B4 00 00                call    _srand
```

v6==0时候 触发0C0000005h

到loc_401119符合

```
.text:00401122 058 81 7D D0 05 00 00 C0          cmp     [ebp+var_30], 0C0000005h


.text:0040112B 058 68 E8 07 00 00                push    7E8h                            ; Seed
.text:00401130 05C E8 C8 B4 00 00                call    _srand
```

就是以7E8h为seed 调用了srand 

然后是v6!=0:

```
.text:00401129 058 75 0F                         jnz     short loc_40113A

.text:0040113A                                   loc_40113A:                             ; CODE XREF: __scrt_common_main_seh(void)+129↑j
.text:0040113A 058 81 7D D0 94 00 00 C0          cmp     [ebp+var_30], 0C0000094h
.text:00401141 058 75 0B                         jnz     short loc_40114E
.text:00401141
.text:00401143 058 E8 94 B4 00 00                call    _rand
.text:00401143
.text:00401148 058 03 45 E4                      add     eax, [ebp+var_1C]
.text:0040114B 058 89 45 E4                      mov     [ebp+var_1C], eax
```

我怕汇编不好理解

```
.text:00401143 058 E8 94 B4 00 00                call    _rand
.text:00401143
.text:00401148 058 03 45 E4                      add     eax, [ebp+var_1C]
.text:0040114B 058 89 45 E4                      mov     [ebp+var_1C], eax
```

这我也讲一下

首先call的结果是放eax里面

然后 add 是结果存到前一个参数

mov是右边的值放左边

其实就是 ebp+rand()->ebp

这不就是累加嘛

于是知道了 v6!=0的时候就是给这个ebp-1C累加喽

那这个是谁？

unsigned int v6; // [esp+38h] {{{[ebp-1Ch]}}}

所以就是v6!=0给v6+=rand()

ok seh分析完成！

回到

```
unsigned int __cdecl __scrt_common_main_seh(unsigned int *a1, int a2)
{
  int i; // [esp+2Ch] [ebp-28h]
  unsigned int v4; // [esp+30h] [ebp-24h]
  unsigned int v5; // [esp+34h] [ebp-20h]
  unsigned int v6; // [esp+38h] [ebp-1Ch]

  v5 = *a1;
  v4 = a1[1];
  v6 = 0;
  for ( i = 0; i < 32; ++i )
  {
    v5 += (*(_DWORD *)(a2 + 4 * (v6 & 3)) + v6) ^ (v4 + ((v4 >> 5) ^ (16 * v4)));
    if ( !v6 )
      MEMORY[0] = 0;
    v6 -= 1640531527;
    v4 += (*(_DWORD *)(a2 + 4 * ((v6 >> 11) & 3)) + v6) ^ (v5 + ((v5 >> 5) ^ (16 * v5)));
  }
  *a1 = v5;
  a1[1] = v4;
  return v4;
}
```

完全TEA

tea还是比较简单的 全部反过来写一次就行

但是要记得v6要先算结果值什么的

我们还需要密文

直接去check找data 

```
unsigned char ciphertext[48] = {
    0x89, 0x11, 0x0B, 0xC2, 0xDE, 0x3A, 0x5D, 0x27,
    0xDE, 0xFC, 0xAD, 0xB1, 0x6D, 0x16, 0x01, 0x82,
    0xDC, 0x08, 0x1E, 0xCD, 0x99, 0x08, 0x83, 0xA0,
    0x06, 0xC7, 0xC8, 0xC7, 0xF5, 0xA9, 0xC9, 0x9F,
    0x1D, 0xA7, 0x50, 0x82, 0x66, 0x9E, 0x32, 0xED,
    0xD7, 0x21, 0x8D, 0xB8, 0x43, 0x3C, 0xDA, 0x2E
};
```

ok

看check函数逆天复杂但其实就是每个位置检查

```
case 2:
    v29 = *a1 - *a2;                    // 比较第一个字节
    if ( v29 )
        v29 = 2 * (v29 > 0) - 1;        // 如果不相等，返回 1 或 -1
    if ( v29 )
        return v29;                      // 有差异就立即返回
    
    v30 = a1[1];                         // 取第一个数组的第二个字节
    v31 = a2[1];                         // 取第二个数组的第二个字节
    goto LABEL_488;

LABEL_488:
    v29 = v30 - v31;                     // 比较第二个字节
    if ( v29 )
        return 2 * (v29 > 0) - 1;        // 不相等则返回 1 或 -1
    return v29;                          // 相等则返回 0
```

随手举的例子

密文也有了

直接exp

```
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// 48字节密文（从 IDA 提取）
unsigned char ciphertext[48] = {
    0x89, 0x11, 0x0B, 0xC2, 0xDE, 0x3A, 0x5D, 0x27,
    0xDE, 0xFC, 0xAD, 0xB1, 0x6D, 0x16, 0x01, 0x82,
    0xDC, 0x08, 0x1E, 0xCD, 0x99, 0x08, 0x83, 0xA0,
    0x06, 0xC7, 0xC8, 0xC7, 0xF5, 0xA9, 0xC9, 0x9F,
    0x1D, 0xA7, 0x50, 0x82, 0x66, 0x9E, 0x32, 0xED,
    0xD7, 0x21, 0x8D, 0xB8, 0x43, 0x3C, 0xDA, 0x2E
};

uint32_t key[4] = {
    0x114514,    // 1131796
    0x1919810,   // 26318864
    0x39C5BB,    // 3786171
    0xFFE211     // 16769553
};

void tea_decrypt(unsigned int* a1, unsigned int* a2) {
    int i;
    unsigned int v3;  // a1[1]
    unsigned int v4;  // a1[0]
    unsigned int v5;  // sum

    v4 = a1[0];
    v3 = a1[1];

    // 生成随机数序列（32个，第0个为0）
    srand(0x7E8);                 // 2024
    unsigned int randoms[32];
    randoms[0] = 0;             
    for (i = 1; i < 32; i++) {
        randoms[i] = rand();    
    }

    v5 = 0;
    for (i = 0; i < 32; i++) {
        v5 -= 0x61C88647;       
        v5 += randoms[i];        
    }

    for (i = 0; i < 32; i++) {

        v3 -= (a2[(v5 >> 11) & 3] + v5) ^ (v4 + ((v4 >> 5) ^ (16 * v4)));

        // 逆sum更新
        v5 += 0x61C88647;       
        v5 -= randoms[31 - i]; 

        v4 -= (a2[v5 & 3] + v5) ^ (v3 + ((v3 >> 5) ^ (16 * v3)));
    }

    a1[0] = v4;
    a1[1] = v3;
}

int main() {
    // 每8字节一块，共6块
    for (int i = 0; i < 48; i += 8) {
        unsigned int block[2];
        memcpy(block, &ciphertext[i], 8);
        tea_decrypt(block, key);
        memcpy(&ciphertext[i], block, 8);
    }

    printf("Flag: %s\n", ciphertext);
    return 0;
}
```

Flag: flag{Y0u_s0lv3d_thE_Qu3s7I0n_5O_dr1nk_5oMe_t3A}

搞定

