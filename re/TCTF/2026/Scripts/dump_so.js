function dump_so(libName) {
    Java.perform(() => {        
        // // 1. 更可靠地获取模块信息
        var libso = Process.getModuleByName(libName);
        if (!libso) {
            var modules = Process.enumerateModules();
            console.log("[+] 已加载的 SO 文件列表 (" + modules.length + " 个):");
            modules.forEach(function(m, i) {
                console.log("  [" + i + "] " + m.name + "  base=" + m.base + "  size=" + m.size + "  path=" + m.path);
            });
            console.error("[!] 错误：未找到模块 libil2cpp.so");
            return;
        }

        // 2. 验证基地址和大小是否合理
        console.log("[+] 模块基址: " + libso.base);
        console.log("[+] 模块大小: " + libso.size);
        if (libso.size <= 0 || libso.size > 0x10000000) { // 大小合理性检查，例如大于256MB则可疑
            console.error("[!] 模块大小异常，可能获取失败");
            return;
        }

        // 3. 安全地设置内存权限并读取
        try {
            // 修改内存权限为可读
            // var originProtection = 
            Memory.protect(libso.base, libso.size, 'r--');

            // 关键改进：分块读取内存，避免不连续映射区域导致崩溃
            var chunkSize = 0x1000; // 每次读取4KB
            var totalSize = libso.size;
            var file_path = "/sdcard/download/" + libso.name + "_" + libso.base + "_" + ptr(totalSize) + ".so";
            var file_handle = new File(file_path, "wb");

            if (file_handle) {
                for (var offset = 0; offset < totalSize; offset += chunkSize) {
                    var bytesToRead = Math.min(chunkSize, totalSize - offset);
                    try {
                        // 读取内存块
                        var chunk = libso.base.add(offset).readByteArray(bytesToRead);
                        if (chunk !== null) {
                            file_handle.write(chunk);
                        } else {
                            console.warn("[!] 读取的内存块为空，跳过写入");
                        }
                    } catch (e) {
                        // 如果某一块读取失败，用0填充并继续
                        console.warn("[!] 偏移 0x" + offset.toString(16) + " 处读取失败，用0填充");
                        var zeroBuffer = new ArrayBuffer(bytesToRead);
                        file_handle.write(zeroBuffer);
                    }
                }
                file_handle.flush();
                file_handle.close();
                console.log("[dump] 成功: " + file_path);
            }
        } catch (e) {
            console.error("[!] dump_so 过程中发生异常: " + e.message);
        }
    });
}
console.log("[+] 脚本加载时间: " + new Date().toLocaleTimeString());

setTimeout( () => {
  console.log("[+] 回调执行时间: " + new Date().toLocaleTimeString());
  console.log("[+] 延迟后开始 dump...");
  dump_so("libsec2026.so");

}, 10000); // 延迟500毫秒，可根据实际情况调整
