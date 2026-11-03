// Godot 4.5.1 ARM64，本题 libgodot_android.so 的偏移。
// frida -U -p <游戏PID> -l HookGodotVehicle.js
// 只负责定位 /root/TownScene/InstancePos/car/Body，并在下一次物理同步时瞬移一次。
// 瞬移后自动解除 hook，车辆继续接受输入和物理模拟。
//
// SceneTree + 0x320 = root；Node.name + 0x1E0 = StringName；_Data + 0x08 = UTF-32LE。
// Node.children.size + 0x188；Node.children.data + 0x190。
// RigidBody3D::_sync_body_state RVA 0x264A340。
// PhysicsDirectBodyState3D 虚表：get_transform +0x128，set_transform +0x120。

const MODULE = 'libgodot_android.so';
const SINGLETON = 0x4050b40;       // 模块基址 + RVA：SceneTree::singleton 槽
const ROOT = 0x320;                // SceneTree + 0x320：root
const NAME = 0x1e0;                // Node + 0x1E0：StringName
const CHILD_COUNT = 0x188;         // Node + 0x188：children 数量
const CHILD_DATA = 0x190;          // Node + 0x190：children 数组
const SYNC_BODY = 0x264a340;       // 模块基址 + RVA：RigidBody3D::_sync_body_state
const MTE = ptr('0x00ffffffffffffff');
const TARGET_PATH = '/root/TownScene/InstancePos/car/Body';
const TELEPORT_X = -14.1395;
const TELEPORT_Y = 11.8164;
const TELEPORT_Z = -3.9586;

function clean(value) { return ptr(value).and(MTE); }

function nodeName(node) {
    const data = clean(clean(node).add(NAME).readPointer());
    const chars = clean(data.add(8).readPointer());
    let text = '';
    for (let i = 0; i < 128; i++) {
        const c = chars.add(i * 4).readU32();
        if (c === 0) return text;
        text += String.fromCodePoint(c);
    }
    return text;
}

function findBody(base) {
    const tree = clean(base.add(SINGLETON).readPointer());
    if (tree.isNull()) return null;
    const root = clean(tree.add(ROOT).readPointer());
    if (root.isNull()) return null;
    const stack = [{ node: root, path: '' }];
    while (stack.length) {
        const item = stack.pop();
        const node = clean(item.node);
        const path = item.path + '/' + nodeName(node);
        if (path === TARGET_PATH) return node;
        const count = node.add(CHILD_COUNT).readU32();
        const children = clean(node.add(CHILD_DATA).readPointer());
        for (let i = count - 1; i >= 0; i--) {
            stack.push({ node: children.add(i * Process.pointerSize).readPointer(), path: path });
        }
    }
    return null;
}

function HookGodotVehicle(x, y, z) {
    const base = Process.getModuleByName(MODULE).base;
    const body = findBody(base);
    if (!body) throw new Error('target not found: ' + TARGET_PATH);
    const xyz = [x, y, z].map(Number).map(Math.fround);
    if (!xyz.every(Number.isFinite)) throw new Error('coordinates must be finite');

    const transform = Memory.alloc(48); // basis 36 字节，origin 位于 +0x24
    let hit = false;
    const hook = Interceptor.attach(base.add(SYNC_BODY), {
        onEnter(args) {
            if (hit || !clean(args[0]).equals(body)) return;
            hit = true;
            const state = args[1];
            const vtable = clean(state.and(MTE).readPointer());
            const getTransform = new NativeFunction(vtable.add(0x128).readPointer(), Array(12).fill('float'), ['pointer']);
            const setTransform = new NativeFunction(vtable.add(0x120).readPointer(), 'void', ['pointer', 'pointer']);
            const values = getTransform(state);
            for (let i = 0; i < 9; i++) transform.add(i * 4).writeFloat(values[i]);
            transform.add(0x24).writeFloat(xyz[0]);
            transform.add(0x28).writeFloat(xyz[1]);
            transform.add(0x2c).writeFloat(xyz[2]);
            setTransform(state, transform);
            this.teleported = true;
        },
        onLeave() {
            if (this.teleported) {
                hook.detach();
                console.log('[HookGodotVehicle] teleported once; hook detached');
            }
        }
    });
    console.log('[HookGodotVehicle] Body=' + body + ' -> [' + xyz.join(', ') + ']');
}

HookGodotVehicle(TELEPORT_X, TELEPORT_Y, TELEPORT_Z);
