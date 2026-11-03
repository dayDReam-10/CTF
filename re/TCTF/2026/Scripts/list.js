// Godot 4.5.1 ARM64，本题 libgodot_android.so 的偏移。
// frida -U -p <游戏PID> -l list.js
// 只列出 SceneTree::current_scene 及其全部后代节点。
const MODULE = 'libgodot_android.so';
const SCENETREE_SINGLETON = 0x4050b40; // 模块基址 + RVA：SceneTree::singleton，读取 SceneTree*
const CURRENT_SCENE = 0x700;          // SceneTree + 0x700：current_scene，读取当前场景 Node*
const NAME = 0x1e0;                   // Node + 0x1E0：name（StringName，内部保存 _Data*）
const CHILD_COUNT = 0x188;            // Node + 0x188：children 数量，u32
const CHILD_DATA = 0x190;             // Node + 0x190：children 数组首地址，Node**，每项 8 字节
const MTE = ptr('0x00ffffffffffffff'); // Android MTE：读指针前去除高字节 tag

function ListCurrentScene() {
    const base = Process.getModuleByName(MODULE).base;
    const tree = base.add(SCENETREE_SINGLETON).readPointer().and(MTE);
    if (tree.isNull()) return [];

    const root = tree.add(CURRENT_SCENE).readPointer();
    if (root.isNull()) return [];

    const objects = [];
    const stack = [{ node: root, parentPath: '/root' }];
    while (stack.length) {
        const item = stack.pop();
        const node = item.node;
        const memory = node.and(MTE);

        // Node.name -> StringName::_Data -> String 字符指针（UTF-32LE）。
        const data = memory.add(NAME).readPointer().and(MTE);
        let text = '';
        if (!data.isNull()) {
            let chars = data.add(0x08).readPointer().and(MTE);
            if (!chars.isNull()) {
                for (let c = chars.readU32(); c !== 0; c = chars.readU32()) {
                    text += String.fromCodePoint(c);
                    chars = chars.add(4);
                }
            }
        }

        const path = item.parentPath + '/' + text;
        const object = { name: text, path: path, address: node };
        objects.push(object);
        console.log(text + '  ' + path + '  ' + node);

        const count = memory.add(CHILD_COUNT).readU32();
        const children = memory.add(CHILD_DATA).readPointer().and(MTE);
        for (let i = count - 1; i >= 0; i--) {
            stack.push({
                node: children.add(i * Process.pointerSize).readPointer(),
                parentPath: path
            });
        }
    }
    return objects;
}

console.log('[list] current_scene nodes:');
ListCurrentScene();
