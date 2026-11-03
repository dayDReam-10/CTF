// Godot 4.5.1 ARM64，本题 libgodot_android.so 的偏移。
// frida -U -p <游戏PID> -l FindNodeByName.js
// FindNodeByName("Body") -> 当前场景中所有同名节点 [{ name, path, address: Node* }]，未找到返回 []。
const MODULE = 'libgodot_android.so';
const SCENETREE_SINGLETON = 0x4050b40; // 模块基址 + RVA：SceneTree::singleton，读取 SceneTree*
// SceneTree + 0x320：root（总根节点）；本脚本只遍历下面的 current_scene。
const CURRENT_SCENE = 0x700;          // SceneTree + 0x700：current_scene，读取当前场景 Node*
const NAME = 0x1e0;                   // Node + 0x1E0：name（StringName，内部保存 _Data*）
const CHILD_COUNT = 0x188;            // Node + 0x188：children 数量，u32
const CHILD_DATA = 0x190;             // Node + 0x190：children 数组首地址，Node**，每项 8 字节
const MTE = ptr('0x00ffffffffffffff'); // JS 读内存前去除指针高字节 tag

function FindNodeByName(wantedName) {
    // 模块 -> singleton 全局槽 -> SceneTree -> current_scene。
    const base = Process.getModuleByName(MODULE).base;
    const tree = base.add(SCENETREE_SINGLETON).readPointer().and(MTE);
    if (tree.isNull()) return [];
    const root = tree.add(CURRENT_SCENE).readPointer();
    if (root.isNull()) return [];

    // 深度优先遍历全部节点；结果保留原始 Node*，仅在读内存时去除 tag。
    const objects = [];
    const stack = [{ node: root, parentPath: '/root' }];
    while (stack.length) {
        const { node, parentPath } = stack.pop();
        const memory = node.and(MTE);

        // Node.name -> StringName::_Data -> String 字符指针（UTF-32LE）。
        const data = memory.add(NAME).readPointer().and(MTE);
        let text = '';
        if (!data.isNull()) {
            let chars = data.add(0x08).readPointer().and(MTE);
            if (!chars.isNull()) {
                for (let c = chars.readU32(); c !== 0; c = chars.readU32()) {
                    text += String.fromCodePoint(c);
                    chars = chars.add(4); // char32_t，每字符 4 字节
                }
            }
        }
        const path = parentPath + '/' + text;
        if (text === wantedName) objects.push({ name: text, path, address: node });

        // 直接读取子节点数组，逆序入栈，让第一个 child 优先被访问。
        const count = memory.add(CHILD_COUNT).readU32();
        const children = memory.add(CHILD_DATA).readPointer().and(MTE);
        for (let i = count - 1; i >= 0; i--) {
            stack.push({ node: children.add(i * Process.pointerSize).readPointer(), parentPath: path });
        }
    }
    return objects;
}
