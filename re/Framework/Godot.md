# Godot的基本框架分析

Godot游戏与UE引擎有异有同，godot的布局偏移随着平台或者各种条件变化较大，不像UE一般可以直接地dump sdk，不好直接如同UE引擎一般小调整深入结构体格局处理，可事实真的如此吗？

## ObjectDB

可以类比成UE中的UObjectarray，包含所有类实例

```cpp
// Godot 4.4 core/object/object.h
class ObjectDB {
    struct ObjectSlot {
        uint64_t validator : 39;     // 对象 ID 的校验值，用于识别槽位是否仍对应原对象
        uint64_t next_free : 24;     // 空闲槽位链表的下一个节点索引
        uint64_t is_ref_counted : 1; // 标记该对象是否属于 RefCounted 体系
        Object *object = nullptr;    // +0x08，实际对象的内存地址
    };

    static ObjectSlot *object_slots; // 全局对象槽位数组，每个槽位对应一个已分配或可复用的索引
    static uint32_t slot_count;      // 当前已注册的对象数量
    static uint32_t slot_max;        // 槽位数组容量，用于检查索引是否越界

public:
    static Object *get_instance(ObjectID p_id);
    static void add_instance(Object *p_object);
    static void remove_instance(Object *p_object);

    // ...
};

static Object *get_instance(ObjectID p_id) {
    uint32_t slot = p_id & 0xFFFFFF;

    if (slot >= slot_max)
        return nullptr;

    // ... 获取锁

    ObjectSlot *s = &object_slots[slot];

    // ... 校验 ObjectID 中的 validator

    Object *obj = s->object;

    // ... 释放锁
    return obj;
}

// ObjectDB::add_instance(Object*)
// object.cpp，搜索 add_instance

void ObjectDB::add_instance(Object *p_object) {
    // ... 查找空闲槽位，必要时扩容

    ObjectSlot *slot = &object_slots[slot_index];
    slot->object = p_object;

    // ... 设置 validator、next_free、is_ref_counted
    // ... 更新 slot_count 并生成 ObjectID
}


// ObjectDB::remove_instance(Object*)
// object.cpp，搜索 remove_instance

void ObjectDB::remove_instance(Object *p_object) {
    // ... 定位对象对应的槽位

    ObjectSlot *slot = &object_slots[slot_index];
    slot->object = nullptr;

    // ... 更新 validator
    // ... 将槽位加入空闲链表
    // ... 更新 slot_count
}

// ObjectDB
//     │
//     ├── slot_count
//     ├── slot_max
//     ├── validator_counter
//     └── object_slots ──→ ObjectSlot 数组
//                              │
//                              ├── [0] ──→ Object*
//                              ├── [1] ──→ Object*
//                              └── [2] ──→ Object*

// Godot 4.4 — core/object/object.h

class Object {
    // vptr: +0x00，8 字节。读它得 vtable 地址，vtable 槽位即虚函数指针
    // 字段偏移按声明顺序在 vptr 之后排列，写逆向脚本读字段全依赖这个顺序
    // vtable 槽位顺序：get_class, is_class, _setv, _getv, _get_property_listv, _validate_propertyv, _property_can_revertv, _property_get_revertv, _notificationv, callp, call_const, ~Object

    ObjectGDExtension *_extension; // 扩展类元信息：类名、父类、虚函数表，扩展类逆向从这里进
    GDExtensionClassInstancePtr _extension_instance; // 扩展实例指针：拿到原生扩展对象
    ObjectID _instance_id; // 走 ObjectDB::get_instance 拿 Object*，所有 ObjectID 引用的反查入口
    ScriptInstance *script_instance; // 走 GDScriptInstance 拿 Vector<Variant>，脚本变量容器入口
    Variant script; // 拿脚本资源，衔接脚本类定义
    const StringName *_class_name_ptr; // 拿 StringName 指针，走 StringNamePool 还原类名

public:
    ObjectID get_instance_id() const; // → ObjectDB::get_instance → Object*
    const StringName &get_class_name() const; // → StringNamePool → 类名 → ClassDB 查类
    ScriptInstance *get_script_instance() const; // → GDScriptInstance → 脚本变量
    virtual String get_class() const; // vtable 槽，读类名字符串
    virtual bool is_class(const String &p_class) const; // vtable 槽，继承链判类型

    void get_method_list(List<MethodInfo> *p_list) const; // → ClassDB 方法表，拿函数签名和 id
    void get_property_list(List<PropertyInfo> *p_list, bool p_reversed = false) const; // → ClassDB 属性表，拿属性名和类型
    virtual ~Object(); //析构
};
```

```cpp
class ScriptInstance {
public:
    virtual bool set(
        const StringName &p_name,
        const Variant &p_value
    ) = 0;                                             // 设置脚本属性

    virtual bool get(
        const StringName &p_name,
        Variant &r_ret
    ) const = 0;                                       // 读取脚本属性

    virtual void get_property_list(
        List<PropertyInfo> *p_properties
    ) const = 0;                                       // 获取脚本属性列表

    virtual Variant::Type get_property_type(
        const StringName &p_name,
        bool *r_is_valid = nullptr
    ) const = 0;                                       // 查询属性类型

    virtual void validate_property(
        PropertyInfo &p_property
    ) const = 0;                                       // 校验或调整属性信息

    virtual bool property_can_revert(
        const StringName &p_name
    ) const = 0;                                       // 判断属性是否可还原

    virtual bool property_get_revert(
        const StringName &p_name,
        Variant &r_ret
    ) const = 0;                                       // 获取属性的还原值

    virtual Object *get_owner() { return nullptr; }    // 获取所属 Object

    virtual void get_property_state(
        List<Pair<StringName, Variant>> &state
    );                                                 // 导出属性状态

    virtual void get_method_list(
        List<MethodInfo> *p_list
    ) const = 0;                                       // 获取脚本方法列表

    virtual bool has_method(
        const StringName &p_method
    ) const = 0;                                       // 检查脚本是否存在指定方法

    virtual Variant callp(
        const StringName &p_method,
        const Variant **p_args,
        int p_argcount,
        Callable::CallError &r_error
    ) = 0;                                             // 调用脚本方法

    virtual void notification(
        int p_notification,
        bool p_reversed = false
    ) = 0;                                             // 处理引擎通知

    virtual Ref<Script> get_script() const = 0;        // 获取关联脚本资源
    virtual ScriptLanguage *get_language() = 0;       // 获取脚本语言实现

    virtual ~ScriptInstance();                         // 虚析构函数
};
//这里都是虚函数，真正的实现位于GDScriptInstance


class GDScriptInstance : public ScriptInstance {
    ObjectID owner_id; // 所属 Object 的 ObjectID
    Object *owner; // 所属 Object 指针
    Ref<GDScript> script; // 对应的 GDScript 资源，比对目标脚本用
    Vector<Variant> members; // 所有实例变量值，按 MemberInfo::index 索引，脚本变量容器
    bool base_ref_counted; // 基类是否 RefCounted

public:
    virtual Object *get_owner() { return owner; } // 读所属 Object
    virtual bool set(const StringName &p_name, const Variant &p_value) override; // 按名写成员，查 member_indices 得 index 后写 members
    virtual bool get(const StringName &p_name, Variant &r_ret) const override; // 按名读成员
    virtual void get_property_list(List<PropertyInfo> *p_properties) const override; // 枚举成员属性
    virtual Variant::Type get_property_type(const StringName &p_name, bool *r_is_valid = nullptr) const override; // 读成员类型
    virtual Variant callp(const StringName &p_method, const Variant **p_args, int p_argcount, Callable::CallError &r_error) override; // 调脚本方法
    virtual Ref<Script> get_script() const override; // 读脚本资源
    virtual void notification(int p_notification, bool p_reversed = false) override; // 脚本侧通知处理
    Variant debug_get_member_by_index(int p_idx) const; // index→成员值，直接读 members[p_idx]
    String to_string(bool *r_valid); // 转字符串
    void reload_members(); // 热重载时重建 members
};
```

```cpp
struct GDScript::MemberInfo {
    int index; // 成员在 GDScriptInstance::members 数组中的索引
    StringName setter; // 属性 setter 方法名
    StringName getter; // 属性 getter 方法名
    GDScriptDataType data_type; // 成员静态类型，解析 Variant 时校验用
    PropertyInfo property_info; // 属性元信息，含名字、类型、hint
};

class GDScript : public Script {
    Ref<GDScriptNativeClass> native; // 对应的原生类，instance_base_type 来源
    Ref<GDScript> base; // 基类脚本引用
    GDScript *_base; // 基类脚本裸指针，快速访问
    GDScript *_owner; // 所属根脚本，内部类时指向外层

    HashMap<StringName, MemberInfo> member_indices; // 所有实例变量(含基类)名→MemberInfo，变量名到 index 的映射表
    HashSet<StringName> members; // 仅当前类声明的实例变量名

    HashMap<StringName, MemberInfo> static_variables_indices; // 静态变量名→MemberInfo
    Vector<Variant> static_variables; // 静态变量值，全局按 index 存储

    HashMap<StringName, Variant> constants; // 常量表
    HashMap<StringName, GDScriptFunction *> member_functions; // 成员方法名→函数对象，方法名到字节码入口
    HashMap<StringName, Ref<GDScript>> subclasses; // 内部类名→子脚本
    HashMap<StringName, MethodInfo> _signals; // 脚本自定义信号
    Dictionary rpc_config; // RPC 配置

    HashMap<GDScriptFunction *, LambdaInfo> lambda_info; // lambda 捕获信息
    List<UpdatableFuncPtr *> func_ptrs_to_update; // 热重载时需更新的函数指针

    GDScriptFunction *initializer; // _init() 直接指针，实例化入口
    GDScriptFunction *implicit_initializer; // @implicit_new()
    GDScriptFunction *implicit_ready; // @implicit_ready()
    GDScriptFunction *static_initializer; // @static_initializer()

    int subclass_count; // 子类数量
    RBSet<Object *> instances; // 该脚本的所有实例，反查目标脚本的全部实例
    bool destructing; // 是否正在析构
    bool clearing; // 是否正在清理

    String source; // 脚本源码
    Vector<uint8_t> binary_tokens; // 编译后的字节码 token，逆向函数体入口
    String path; // 脚本资源路径
    StringName local_name; // 内部类标识或 class_name
    StringName global_name; // class_name 全局名
    String fully_qualified_name; // 全限定名
    String simplified_icon_path; // 图标路径
    SelfList<GDScript> script_list; // 全局脚本链表节点

public:
    const HashMap<StringName, MemberInfo> &debug_get_member_indices() const; // 读 member_indices，变量名→index
    const HashMap<StringName, GDScriptFunction *> &debug_get_member_functions() const; // 读成员方法表
    StringName debug_get_member_by_index(int p_idx) const; // index→变量名，反向映射
    StringName debug_get_static_var_by_index(int p_idx) const; // index→静态变量名
    Ref<GDScript> get_base() const; // 读基类脚本，沿继承链向上
    Ref<Script> get_base_script() const; // 读基类脚本(Ref<Script>)
    const HashMap<StringName, Ref<GDScript>> &get_subclasses() const; // 读内部类
    const HashMap<StringName, Variant> &get_constants() const; // 读常量表
    const HashSet<StringName> &get_members() const; // 读当前类成员名
    const Ref<GDScriptNativeClass> &get_native() const; // 读原生类
    const GDScriptDataType &get_member_type(const StringName &p_member) const; // 读成员静态类型
    ScriptInstance *instance_create(Object *p_this) override; // 创建 GDScriptInstance，构造入口
    bool instance_has(const Object *p_this) const override; // 判断对象是否为该脚本实例
    String get_script_path() const; // 读脚本路径
    const Vector<uint8_t> &get_binary_tokens_source() const; // 读字节码 token
};
```

```cpp
class ObjectID {
    uint64_t id; // 内部只维护这一个 64 位整数
};

// 生成逻辑：Validator 左移 24 位，然后按位或上 Slot 索引
uint64_t id = validator_counter;
id <<= OBJECTDB_SLOT_MAX_COUNT_BITS; 
id |= uint64_t(slot);
if (is_ref_counted) id |= OBJECTDB_REFERENCE_BIT; // 最高位置 1

 63          62                                        24                   0
 +-----------+-----------------------------------------+--------------------+
 | 引用标记位 |              验证器 (39位)               |   槽位索引 (24位)   |
 +-----------+-----------------------------------------+--------------------+
```

## SceneTree

类似于UE的Gworld，表达当前作用域

```cpp
// https://github.com/godotengine/godot/blob/4.5.1-stable/scene/main/scene_tree.h
// https://github.com/godotengine/godot/blob/4.5.1-stable/scene/main/scene_tree.cpp
//
// 关键函数：
// get_singleton()：取得全局 SceneTree 实例
// get_current_scene()：取得当前主场景根节点
// set_current_scene()：设置当前主场景根节点
// get_root()：取得场景树的根窗口


// 1  与当前场景直接相关的布局字段
// scene/main/scene_tree.h

class SceneTree : public MainLoop {
private:
    // ...

    Window *root = nullptr;
    // 场景树的根窗口
    // 当前主场景挂在它下面

    // ...

    Node *current_scene = nullptr;
    // 当前主场景根节点
    // 角色、敌人等关卡节点位于这个场景的子树中

    // ...

    static SceneTree *singleton;
    // 全局 SceneTree 实例指针
    // 静态存储，所有代码通过这个成员取得同一个已登记实例

public:
    static SceneTree *get_singleton() {
        return singleton;
    }

    Window *get_root() const {
        return root;
    }

    Node *get_current_scene() const;
    void set_current_scene(Node *p_scene);

    // ...
};


// 2  读取当前主场景
// scene/main/scene_tree.cpp

Node *SceneTree::get_current_scene() const {
    return current_scene;
    // 直接返回成员中保存的 Node*
}


// 3  设置当前主场景
// scene/main/scene_tree.cpp

void SceneTree::set_current_scene(Node *p_scene) {
    ERR_FAIL_COND_MSG(
            !Thread::is_main_thread(),
            "Changing scene can only be done from the main thread.");
    // 场景设置在主线程执行

    ERR_FAIL_COND(
            p_scene && p_scene->get_parent() != root);
    // 非空场景的父节点必须是 root

    current_scene = p_scene;
    // 更新当前主场景指针
    // 这个函数只登记当前场景，接入节点树由 add_child() 完成
}

// 模块基址
//     │
//     └── singleton 全局变量偏移【需要实际偏移】
//          │
//          ▼
//        SceneTree::singleton
//          │
//          │ 读取保存的 SceneTree*
//          ▼
//        SceneTree 实例
//          │
//          └── current_scene【需要实际偏移】
//               │
//               ▼
//             当前主场景根 Node
//               │
//               └── data.children / children_cache【需要实际偏移】
//                    │
//                    ├── 子节点容器内部布局【需要实际偏移】
//                    │
//                    └── 逐层遍历子节点
//                         │
//                         │ 读取 data.name 匹配节点名称【需要实际偏移】
//                         ▼
//                       Player 节点
//                         │
//                         └── Object.script_instance【需要实际偏移】
//                              │
//                              ▼
//                            GDScriptInstance
//                              │
//                              ├── owner【需要实际偏移】
//                              │    └── 原 Player 对象
//                              │
//                              ├── script【需要实际偏移】
//                              │    │
//                              │    └── 引用内部的脚本指针【需要实际偏移】
//                              │         │
//                              │         ▼
//                              │       GDScript 脚本定义
//                              │         │
//                              │         └── member_indices【需要实际偏移】
//                              │              │
//                              │              └── 哈希表条目布局【需要实际偏移】
//                              │                   │
//                              │                   ├── "hp" → MemberInfo
//                              │                   │           └── index【需要实际偏移】
//                              │                   │                └── 读取索引值 i
//                              │                   │
//                              │                   └── "speed" → MemberInfo
//                              │                                 └── index【需要实际偏移】
//                              │                                      └── 读取索引值 j
//                              │
//                              └── members：Vector<Variant>【需要实际偏移】
//                                   │
//                                   └── Vector 内部数据指针【需要实际偏移】
//                                        │
//                                        ▼
//                                      底层 Variant 数组
//                                        │
//                                        │ 元素地址 = 数组首地址 + index × sizeof(Variant)
//                                        │ sizeof(Variant) 需要实际大小
//                                        │
//                                        ├── [i]：hp 对应的 Variant
//                                        │    ├── 类型字段【需要实际偏移】
//                                        │    └── 数值存储位置【需要实际偏移】
//                                        │         └── 写入同类型的新数值
//                                        │              └── 修改 hp
//                                        │
//                                        └── [j]：speed 对应的 Variant
//                                             ├── 类型字段【需要实际偏移】
//                                             └── 数值存储位置【需要实际偏移】
//                                                  └── 写入同类型的新数值
//                                                       └── 修改 speed
```

顺便提到Node与Variant的定义：

```cpp
// Node 对象起始处为 Object 基类（含 vptr），Node 自身字段集中在 data 成员中
// data 在 Node 基址后的具体偏移需在 IDA 中按版本确认
// 逆向遍历 SceneTree 时，从 data.name 匹配节点、data.children_cache 向下走

struct NodeData {
    StringName name; // 节点名，按名字匹配目标实例
    Node *parent; // 父节点指针，向上回溯
    HashMap<StringName, Node *> children; // 子节点映射，按名字直接查子节点
    Vector<Node *> children_cache; // 子节点数组，按顺序深度优先遍历
    Node *owner; // 所属场景根节点，判断节点归属
    SceneTree *tree; // 所属场景树，从任意节点向上拿到全局树
    Viewport *viewport; // 所属视口，定位根 Viewport
    bool inside_tree; // 是否在场景树中，过滤游离节点
    int depth; // 节点深度，辅助路径计算
    int internal_children_front_count_cache; // 前部内部子节点数，修正 children_cache 索引
    int internal_children_back_count_cache; // 后部内部子节点数，修正 children_cache 索引
};

class Node : public Object {
    NodeData data; // 节点数据块，读 Node 字段的入口

public:
    StringName get_name() const; // 读节点名，按名字定位实例
    void set_name(const String &p_name); // 改节点名
    Node *get_parent() const; // 读父节点，向上遍历
    int get_child_count(bool p_include_internal = false) const; // 读子节点数
    Node *get_child(int p_index, bool p_include_internal = false) const; // 按索引读子节点，向下遍历
    Node *get_node_or_null(const NodePath &p_path) const; // 按路径找节点，精确定位
    Node *get_node(const NodePath &p_path) const; // 按路径找节点，不存在报错
    NodePath get_path() const; // 读节点路径，从根到当前节点
    Node *find_child(const String &p_pattern, bool p_recursive = true, bool p_owned = true) const; // 按名字模式递归查找
    bool is_inside_tree() const; // 是否在场景树中，过滤游离节点
    SceneTree *get_tree() const; // 读所属场景树
    void queue_free(); // 标记节点待删除
    // script_instance 在 Object 基类中，从 Node 基址按 Object 布局偏移读取
    // Node 的 vtable 包含 Object 虚函数及 Node 重写的 _notificationv
};
```

```cpp
// https://github.com/godotengine/godot/blob/4.5.1-stable/core/variant/variant.h
// https://github.com/godotengine/godot/blob/4.5.1-stable/core/variant/variant_internal.h
//
// 关键函数：
// get_type()：读取类型标记
// get_int()/get_float()：取得数值地址
// get_vector3()：取得内嵌向量地址
// get_string()/get_array()/get_dictionary()：取得内嵌包装对象
// get_object()：取得 Object* 字段地址
// get_float64_array()：沿引用对象取得连续数组


class Variant {
public:
    // 常用类型节选，保留原编号
    enum Type {
        NIL = 0, BOOL = 1, INT = 2, FLOAT = 3, STRING = 4,
        VECTOR2 = 5, VECTOR3 = 9, OBJECT = 24,
        DICTIONARY = 27, ARRAY = 28,
        PACKED_FLOAT64_ARRAY = 33
        // ...
    };

private:
    Type type = NIL; // 类型标记    

    struct ObjData {
        ObjectID id;           // 对象 ID  
        Object *obj = nullptr; // 对象地址
        // ... 引用管理函数
    };

    struct PackedArrayRefBase {
        SafeRefCount refcount;
        // ... 引用管理函数与虚析构
    };

    template <typename T>
    struct PackedArrayRef : public PackedArrayRefBase {
        Vector<T> array; // 连续数组容器
        // ...
    };

    union {
        bool _bool;     // BOOL：直接存值
        int64_t _int;   // INT：64 位整数
        double _float;  // FLOAT：64 位浮点数

        Transform2D *_transform2d;
        ::AABB *_aabb;
        Basis *_basis;
        Transform3D *_transform3d;
        Projection *_projection;
        // 上述类型通过指针访问对象

        PackedArrayRefBase *packed_array;
        // PackedArray 引用对象指针

        void *_ptr;

        uint8_t _mem[
                sizeof(ObjData) > sizeof(real_t) * 4
                        ? sizeof(ObjData) : sizeof(real_t) * 4
        ]{ 0 };
        // 内嵌 String、向量、Array、Dictionary、ObjData 等对象
    } _data alignas(8);
    // 数据区起点，所有联合体成员共享存储区

    ObjData &_get_obj();
    const ObjData &_get_obj() const;

public:
    Type get_type() const { return type; }
};


// 访问实现，省略同类重载
class VariantInternal {
public:
    static int64_t *get_int(Variant *v) {
        return &v->_data._int;
    }

    static double *get_float(Variant *v) {
        return &v->_data._float;
    }

    static Vector3 *get_vector3(Variant *v) {
        return reinterpret_cast<Vector3 *>(v->_data._mem);
    }

    static String *get_string(Variant *v) {
        return reinterpret_cast<String *>(v->_data._mem);
    }

    static Array *get_array(Variant *v) {
        return reinterpret_cast<Array *>(v->_data._mem);
    }

    static Dictionary *get_dictionary(Variant *v) {
        return reinterpret_cast<Dictionary *>(v->_data._mem);
    }

    static Object **get_object(Variant *v) {
        return (Object **)&v->_get_obj().obj;
    }

    static PackedFloat64Array *get_float64_array(Variant *v) {
        return &static_cast<Variant::PackedArrayRef<double> *>(
                v->_data.packed_array)->array;
    }
};


// 存储关系回看：
//
// INT / FLOAT       -> _data 中的直接数值
// VECTOR3           -> _mem 中的向量对象 -> x、y、z
// STRING            -> _mem 中的 String -> 字符存储
// ARRAY / DICTIONARY-> _mem 中的容器包装对象 -> 元素或键值
// OBJECT            -> ObjData -> id、obj
// TRANSFORM3D       -> _transform3d 指针 -> 变换对象
// PACKED_*_ARRAY    -> packed_array -> PackedArrayRef<T> -> Vector<T>
//
// members[index] 的地址 = 数组首地址 + index × sizeof(Variant)
```

## Stringnamepool

```cpp
// https://github.com/godotengine/godot/blob/4.4/core/string/string_name.h
// https://github.com/godotengine/godot/blob/4.4/core/string/string_name.cpp
//
// 关键函数：
// StringName::StringName()：用 hash & MASK 定位 _table 槽，沿 next 比对 hash 和字符串
// StringName::unref()：refcount 归零时从 _table 摘除并 memdelete
// StringName::get_name()：cname 非空返回 cname，否则返回 name
// StringName::operator==()：直接比较 _data 指针

// 1  StringName 本体，只有一个 _data 指针
// 比较两个 StringName 就是比较 _data 指针，O(1)
class StringName {
    enum {
        STRING_TABLE_BITS = 16,                    // 4.4 里是 16，旧版本 12
        STRING_TABLE_LEN = 1 << STRING_TABLE_BITS, // 65536
        STRING_TABLE_MASK = STRING_TABLE_LEN - 1,  // 0xFFFF
    };

    struct _Data {
        SafeRefCount refcount;         // 引用计数，归零时节点摘除
        SafeNumeric static_count;      // 静态引用计数，静态字符串用
        const char *cname = nullptr;   // C 字符串指针，静态字符串走这个
        String name;                   // Godot String 对象，动态字符串走这个
#ifdef DEBUG_ENABLED
        uint32_t debug_references = 0; // 仅调试构建，release 无此字段，影响后续偏移
#endif
        int idx = 0;                   // 在 _table 中的槽索引
        uint32_t hash = 0;             // 字符串哈希值
        _Data *prev = nullptr;         // 链表前驱
        _Data *next = nullptr;         // 链表后继
    };

    static _Data *_table[STRING_TABLE_LEN]; // 全局静态数组，每槽一条 _Data 链表

    _Data *_data = nullptr;            // 唯一成员，指向池中节点，空表示空字符串
};

// 2  查找逻辑，算哈希定位槽，沿链表比对
StringName::StringName(const String &p_name) {
    _data = nullptr;
    if (p_name.is_empty()) return;

    MutexLock lock(mutex);

    uint32_t hash = p_name.hash();
    uint32_t idx = hash & STRING_TABLE_MASK;   // 关键衔接：哈希定位槽

    _data = _table[idx];
    while (_data) {
        if (_data->hash == hash && _data->get_name() == p_name) {
            break;                              // 命中已存在节点
        }
        _data = _data->next;
    }

    if (_data) {
        _data->refcount.ref();                  // 已存在，引用计数加一
        return;
    }

    // 不存在，新建节点插到链表头
    _data = memnew(_Data);
    _data->hash = hash;
    _data->idx = idx;
    _data->name = p_name;
    _data->refcount.init();
    _data->next = _table[idx];
    if (_table[idx]) _table[idx]->prev = _data;
    _table[idx] = _data;
}

// 3  引用计数归零时摘除节点
void StringName::unref() {
    if (_data && _data->refcount.unref()) {
        MutexLock lock(mutex);
        if (_data->prev) {
            _data->prev->next = _data->next;
        } else {
            _table[_data->idx] = _data->next;   // 关键衔接：槽头节点被删时更新 _table
        }
        if (_data->next) {
            _data->next->prev = _data->prev;
        }
        memdelete(_data);
    }
    _data = nullptr;
}

// 4  内存关系图
//
// StringName
//   │
//   └── _data ──→ _Data
//                  ├── refcount
//                  ├── cname  （静态字符串，指向 rodata 里的 C 字符串）
//                  ├── name   （动态字符串，Godot String 对象）
//                  ├── idx    （在 _table 中的槽索引）
//                  ├── hash
//                  ├── prev
//                  └── next
//
//
// 两个 StringName 指向同一个 _Data 就是同一个字符串
// 比较 StringName 直接比 _data 指针，不用查表不用还原字符

```

## ClassDB

```cpp

// https://github.com/godotengine/godot/blob/4.4/core/object/class_db.h
// https://github.com/godotengine/godot/blob/4.4/core/object/class_db.cpp
// https://github.com/godotengine/godot/blob/4.4/core/object/method_bind.h

// 关键结构与函数：
// ClassDB：最外层静态类，持有 classes 全局表，所有注册和查询 API 都在这
// ClassInfo：一个类一份，存这个类的方法表、属性表、父类指针、创建函数
// PropertySetGet：属性表的值，存 setter/getter 的 MethodBind*
// MethodBind：方法表的值，基类存方法名，派生类 MethodBindT 存真实 C++ 函数指针
// get_method()：按类名+方法名从 method_map 拿 MethodBind*
// set_property()：按属性名从 property_map 拿 PropertySetGet，调 _setptr

// 1  ClassDB 最外层
class ClassDB {
    // 属性表的值，setter/getter 的函数指针直接存在这
    struct PropertySetGet {
        StringName setter;      // setter 方法名
        StringName getter;      // getter 方法名
        MethodBind *_setptr;    // setter 的 MethodBind*，直接调
        MethodBind *_getptr;    // getter 的 MethodBind*
        Variant::Type type;     // 属性类型
    };
    //一个类一份，存这个类的所有信息
    struct ClassInfo {
        StringName name;                                       // 类名，"Node3D"
        StringName inherits;                                   // 父类名，"Node"
        HashMap<StringName, MethodBind *> method_map;          // 方法名 → MethodBind*
        HashMap<StringName, PropertySetGet> property_map;      // 属性名 → PropertySetGet
        ClassInfo *inherits_ptr = nullptr;                     // 指向父类 ClassInfo，查方法时沿这条链往上
        Object *(*creation_func)() = nullptr;                  // 创建实例的函数指针
    };
    // 全局表，key 是类名，value 是 ClassInfo
    static HashMap<StringName, ClassInfo> classes;
    //  注册方法，把方法名和函数指针写进 method_map
    template <typename T>
    static MethodBind *bind_method(const MethodInfo &p_method, T *p_method_ptr, ...) {
        MethodBindT<T> *mb = memnew(MethodBindT<T>);
        mb->set_name(p_method.name);                          // 方法名
        mb->set_method(p_method_ptr);                         // 真实 C++ 函数指针
        classes[class_name].method_map[p_method.name] = mb;   // 写进 method_map
        return mb;
    }
    // 1.5  注册属性，把 setter/getter 的 MethodBind* 写进 property_map
    static void add_property(const StringName &p_class, const PropertyInfo &p_info, const StringName &p_setter, const StringName &p_getter) {
        ClassInfo *type = classes.getptr(p_class);
        PropertySetGet psg;
        psg.setter = p_setter;
        psg.getter = p_getter;
        psg._setptr = type->method_map.getptr(p_setter) ? *type->method_map.getptr(p_setter) : nullptr;
        psg._getptr = type->method_map.getptr(p_getter) ? *type->method_map.getptr(p_getter) : nullptr;
        psg.type = p_info.type;
        type->property_map[p_info.name] = psg;                // 写进 property_map
    }
    // 1.6  查方法，遍历继承链从 method_map 拿 MethodBind*
    static MethodBind *get_method(const StringName &p_class, const StringName &p_name) {
        ClassInfo *type = classes.getptr(p_class);           // 从 classes 拿 ClassInfo
        while (type) {
            MethodBind **method = type->method_map.getptr(p_name); // 在 method_map 里查
            if (method && *method) return *method;           // 命中，返回 MethodBind*
            type = type->inherits_ptr;                       // 没找到，跳父类
        }
        return nullptr;
    }

    // 1.7  查属性，遍历继承链从 property_map 拿 PropertySetGet，调 _setptr
    static bool set_property(Object *p_object, const StringName &p_property, const Variant &p_value) {
        ClassInfo *type = classes.getptr(p_object->get_class_name());
        while (type) {
            PropertySetGet *psg = type->property_map.getptr(p_property); // 在 property_map 里查
            if (psg && psg->_setptr) {
                const Variant *argptrs[1] = { &p_value };
                Callable::CallError ce;
                psg->_setptr->call(p_object, argptrs, 1, ce); // 直接调 _setptr
                return true;
            }
            type = type->inherits_ptr;                       // 没找到，跳父类
        }
        return false;
    }
    // 1.8  创建实例，调 creation_func
    static Object *instantiate(const StringName &p_class) {
        ClassInfo *type = classes.getptr(p_class);
        while (type) {
            if (type->creation_func) return type->creation_func();
            type = type->inherits_ptr;
        }
        return nullptr;
    }
};

// 2  MethodBind 基类，method_map 的值

class MethodBind {
    StringName name;              // 方法名
    StringName instance_class;    // 所属类名
    int argument_count = 0;       // 参数个数
};

// 3  MethodBindT 派生类，真实函数指针在这

template <typename T>
class MethodBindT : public MethodBind {
    void (T::*method)(...);       // 真实 C++ 函数指针
};

// 4  调用链
// 脚本调 node.get_class()
//   → Object::callp
//   → ClassDB::get_method("Object", "get_class")      // 第一层：ClassDB
//   → classes["Object"] → ClassInfo                    // 第二层：ClassInfo
//   → ClassInfo::method_map["get_class"] → MethodBind* // 第三层：method_map
//   → MethodBindT::method → &Object::get_class         // 第四层：MethodBindT
//
// 脚本调 node.set("position", v)
//   → Object::set
//   → ClassDB::set_property(node, "position", v)       // 第一层：ClassDB
//   → classes["Node3D"] → ClassInfo                    // 第二层：ClassInfo
//   → ClassInfo::property_map["position"] → PropertySetGet // 第三层：property_map
//   → PropertySetGet::_setptr → MethodBindT::method → &Node3D::set_position // 第四层
//
// 脚本调 Node.new()
//   → ClassDB::instantiate("Node")
//   → classes["Node"] → ClassInfo
//   → ClassInfo::creation_func → 构造实例
```

## PCK资源加载与加解密机制

```cpp
// https://github.com/godotengine/godot/blob/4.4/core/io/resource_loader.cpp
// https://github.com/godotengine/godot/blob/4.4/modules/gdscript/gdscript.cpp
// https://github.com/godotengine/godot/blob/4.4/modules/gdscript/gdscript_cache.cpp
// https://github.com/godotengine/godot/blob/4.4/core/config/project_settings.cpp
// https://github.com/godotengine/godot/blob/4.4/core/io/file_access_pack.cpp
// https://github.com/godotengine/godot/blob/4.4/core/io/file_access.cpp
// https://github.com/godotengine/godot/blob/4.4/core/io/file_access_encrypted.cpp

// 关键函数：
// ResourceLoader::load()：资源加载总入口，创建加载任务并等待加载完成
// ResourceLoader::_load()：遍历格式加载器，通过 recognize_path() 找到能处理该路径的加载器
// ResourceFormatLoaderGDScript::load()：接手 .gd/.gdc 脚本，调用 GDScriptCache::get_full_script()
// GDScriptCache::get_full_script()：查询完整脚本缓存，未命中时进入 get_shallow_script()
// GDScriptCache::get_shallow_script()：识别 .gdc，调用 get_binary_tokens() 读取字节
// GDScriptCache::get_binary_tokens()：调用 FileAccess::open() 并读取文件内容
// ProjectSettings::_load_resource_pack()：挂载 PCK 时调用 PackedData::add_pack()
// PackedSourcePCK::try_open_pack()：解析 PCK 头和目录，分别处理目录加密与文件加密标志
// FileAccess::open()：先通过 PackedData 查找资源路径，找到后返回 PCK 文件访问对象
// FileAccessPack::FileAccessPack()：定位 PCK 中的文件数据，遇到加密条目时调用 open_and_parse()
// FileAccessEncrypted::open_and_parse()：读取加密头、用 AES-256-CFB 解密、校验 MD5，并提供明文

// 1  ResourceLoader::load() 是资源加载的起点
// 这里不会直接读取文件，而是启动并完成一个加载任务
Ref<Resource> ResourceLoader::load(
        const String &p_path,
        const String &p_type_hint,
        ResourceFormatLoader::CacheMode p_cache_mode,
        Error *r_error) {
    LoadThreadMode thread_mode = LOAD_THREAD_FROM_CURRENT;

    // 创建加载任务
    Ref<LoadToken> load_token =
            _load_start(p_path, p_type_hint, thread_mode, p_cache_mode);

    if (load_token.is_null()) {
        if (r_error) {
            *r_error = FAILED;
        }
        return Ref<Resource>();
    }

    // 等待任务完成，实际资源加载会继续进入 _load()
    Ref<Resource> res = _load_complete(*load_token.ptr(), r_error);
    return res;
}

// 2  ResourceLoader::_load() 选择具体资源格式加载器
// 这里按路径和类型提示遍历已注册的 ResourceFormatLoader
Ref<Resource> ResourceLoader::_load(
        const String &p_path,
        const String &p_original_path,
        const String &p_type_hint,
        ResourceFormatLoader::CacheMode p_cache_mode,
        Error *r_error,
        bool p_use_sub_threads,
        float *r_progress) {
    const String &original_path =
            p_original_path.is_empty() ? p_path : p_original_path;

    Ref<Resource> res;

    // 关键衔接：不是直接 find_loader()
    // 而是逐个询问加载器是否 recognize_path()
    for (int i = 0; i < loader_count; i++) {
        if (!loader[i]->recognize_path(p_path, p_type_hint)) {
            continue;
        }

        res = loader[i]->load(
                p_path,
                original_path,
                r_error,
                p_use_sub_threads,
                r_progress,
                p_cache_mode);

        if (res.is_valid()) {
            break;
        }
    }

    return res;
}

// 3  GDScript 加载器接手 .gd 和 .gdc
// ResourceFormatLoaderGDScript::get_recognized_extensions()
// 把 gd、gdc 注册为它能处理的扩展名
Ref<Resource> ResourceFormatLoaderGDScript::load(
        const String &p_path,
        const String &p_original_path,
        Error *r_error,
        bool p_use_sub_threads,
        float *r_progress,
        CacheMode p_cache_mode) {
    Error err;

    bool ignoring =
            p_cache_mode == CACHE_MODE_IGNORE
            || p_cache_mode == CACHE_MODE_IGNORE_DEEP;

    // 关键衔接：交给 GDScriptCache 加载和缓存脚本
    Ref<GDScript> scr = GDScriptCache::get_full_script(
            p_original_path,
            err,
            "",
            ignoring);

    if (r_error) {
        *r_error = scr.is_valid() ? OK : err;
    }

    return scr;
}

// 4  GDScriptCache::get_full_script() 缓存未命中时继续往下走
Ref<GDScript> GDScriptCache::get_full_script(
        const String &p_path,
        Error &r_error,
        const String &p_owner,
        bool p_update_from_disk) {
    MutexLock lock(singleton->mutex);

    Ref<GDScript> script;
    r_error = OK;

    if (singleton->full_gdscript_cache.has(p_path)) {
        script = singleton->full_gdscript_cache[p_path];

        if (!p_update_from_disk) {
            return script;
        }
    }

    if (script.is_null()) {
        // 关键衔接：缓存未命中，读取浅层脚本
        script = get_shallow_script(p_path, r_error);

        if (script.is_null()) {
            return script;
        }
    }

    // reload() 继续完成脚本的解析和加载
    r_error = script->reload(true);

    if (r_error) {
        return script;
    }

    singleton->full_gdscript_cache[p_path] = script;
    singleton->shallow_gdscript_cache.erase(p_path);

    return script;
}

// 5  get_shallow_script() 对 .gdc 和 .gd 分流
Ref<GDScript> GDScriptCache::get_shallow_script(
        const String &p_path,
        Error &r_error,
        const String &p_owner) {
    MutexLock lock(singleton->mutex);

    if (singleton->full_gdscript_cache.has(p_path)) {
        return singleton->full_gdscript_cache[p_path];
    }

    if (singleton->shallow_gdscript_cache.has(p_path)) {
        return singleton->shallow_gdscript_cache[p_path];
    }

    // 路径重映射后再判断扩展名
    const String remapped_path = ResourceLoader::path_remap(p_path);

    Ref<GDScript> script;
    script.instantiate();
    script->set_path(p_path, true);

    if (remapped_path.get_extension().to_lower() == "gdc") {
        // .gdc 是二进制脚本 token
        // 关键衔接：开始读取文件字节
        Vector<uint8_t> buffer = get_binary_tokens(remapped_path);

        if (buffer.is_empty()) {
            r_error = ERR_FILE_CANT_READ;
        }

        script->set_binary_tokens_source(buffer);
    } else {
        // .gd 则直接读取文本源码
        r_error = script->load_source_code(remapped_path);
    }

    if (r_error) {
        return Ref<GDScript>();
    }

    singleton->shallow_gdscript_cache[p_path] = script;
    return script;
}

// 6  get_binary_tokens() 通过 FileAccess::open() 读取 .gdc
Vector<uint8_t> GDScriptCache::get_binary_tokens(const String &p_path) {
    Vector<uint8_t> buffer;
    Error err = OK;

    // 关键衔接：进入通用文件访问层
    Ref<FileAccess> f =
            FileAccess::open(p_path, FileAccess::READ, &err);

    if (err != OK) {
        return buffer;
    }

    uint64_t len = f->get_length();
    buffer.resize(len);

    uint64_t read = f->get_buffer(buffer.ptrw(), buffer.size());

    if (read != len) {
        return Vector<uint8_t>();
    }

    // 返回给 GDScript 的是 FileAccess 提供的内容
    return buffer;
}

// 7  PCK 在资源读取之前挂载
// 主 PCK 可由引擎启动流程加载
// 外部 PCK 也可以通过 ProjectSettings::load_resource_pack() 加载
bool ProjectSettings::_load_resource_pack(
        const String &p_pack,
        bool p_replace_files,
        int p_offset,
        bool p_main_pack) {
    if (PackedData::get_singleton()->is_disabled()) {
        return false;
    }

    // 关键衔接：进入 PCK 格式识别和解析
    bool ok = PackedData::get_singleton()->add_pack(
            p_pack,
            p_replace_files,
            p_offset) == OK;

    if (!ok) {
        return false;
    }

    // PCK 挂载成功后，资源目录访问使用 DirAccessPack
    if (!using_datapack) {
        DirAccess::make_default<DirAccessPack>(
                DirAccess::ACCESS_RESOURCES);
        using_datapack = true;
    }

    return true;
}

// PackedData::add_pack() 把解析交给 PackSource
Error PackedData::add_pack(
        const String &p_path,
        bool p_replace_files,
        uint64_t p_offset) {
    for (int i = 0; i < sources.size(); i++) {
        // 关键衔接：PCK source 开始解析
        if (sources[i]->try_open_pack(
                p_path,
                p_replace_files,
                p_offset)) {
            return OK;
        }
    }

    return ERR_FILE_UNRECOGNIZED;
}

// 8  try_open_pack() 找 PCK 头并解析目录
bool PackedSourcePCK::try_open_pack(
        const String &p_path,
        bool p_replace_files,
        uint64_t p_offset) {
    Ref<FileAccess> f = FileAccess::open(p_path, FileAccess::READ);

    if (f.is_null()) {
        return false;
    }

    // 先在传入偏移处检查 PCK 魔数
    f->seek(p_offset);
    uint32_t magic = f->get_32();

    bool pck_header_found = magic == PACK_HEADER_MAGIC;

    // 如果独立文件开头没有 PCK 头
    // 还会尝试查找嵌入可执行文件中的 PCK
    if (!pck_header_found) {
        // 实际源码还会检查可执行文件中的 PCK section 和文件尾部
        // 找到头后继续解析
    }

    if (!pck_header_found) {
        return false;
    }

    // 记录 PCK 起点，后续用于计算文件数据的实际偏移
    int64_t pck_start_pos = f->get_position() - 4;

    uint32_t version = f->get_32();
    uint32_t ver_major = f->get_32();
    uint32_t ver_minor = f->get_32();
    f->get_32(); // patch

    // PCK 格式版本和引擎版本检查
    ERR_FAIL_COND_V(version != PACK_FORMAT_VERSION, false);
    ERR_FAIL_COND_V(
            ver_major > VERSION_MAJOR
            || (ver_major == VERSION_MAJOR
                && ver_minor > VERSION_MINOR),
            false);

    uint32_t pack_flags = f->get_32();
    uint64_t file_base = f->get_64();

    bool enc_directory =
            (pack_flags & PACK_DIR_ENCRYPTED) != 0;

    bool rel_filebase =
            (pack_flags & PACK_REL_FILEBASE) != 0;

    // 跳过固定保留字段
    for (int i = 0; i < 16; i++) {
        f->get_32();
    }

    // 文件数量位于目录内容之前
    int file_count = f->get_32();

    if (rel_filebase) {
        file_base += pck_start_pos;
    }

    // 目录级加密在挂载阶段发生
    if (enc_directory) {
        Ref<FileAccessEncrypted> fae;
        fae.instantiate();

        Vector<uint8_t> key;
        key.resize(32);

        for (int i = 0; i < key.size(); i++) {
            key.write[i] = script_encryption_key[i];
        }

        // PCK 内的目录数据不带 GDEC 魔数
        Error err = fae->open_and_parse(
                f,
                key,
                FileAccessEncrypted::MODE_READ,
                false);

        if (err != OK) {
            return false;
        }

        // 后续目录字段从解密后的 FileAccess 读取
        f = fae;
    }

    // 逐项读取路径、偏移、长度、MD5 和文件标志
    for (int i = 0; i < file_count; i++) {
        uint32_t path_length = f->get_32();

        CharString cs;
        cs.resize(path_length + 1);
        f->get_buffer(
                reinterpret_cast<uint8_t *>(cs.ptr()),
                path_length);
        cs[path_length] = 0;

        String path;
        path.parse_utf8(cs.ptr(), path_length);

        uint64_t offset = f->get_64();
        uint64_t size = f->get_64();

        uint8_t md5[16];
        f->get_buffer(md5, 16);

        uint32_t flags = f->get_32();

        // 把文件元数据登记到 PackedData
        // PACK_FILE_ENCRYPTED 在这里变成 PackedFile.encrypted
        PackedData::get_singleton()->add_path(
                p_path,
                path,
                file_base + offset + p_offset,
                size,
                md5,
                this,
                p_replace_files,
                (flags & PACK_FILE_ENCRYPTED) != 0);
    }

    return true;
}

// 9  FileAccess::open() 查找 PCK 中的资源
Ref<FileAccess> FileAccess::open(
        const String &p_path,
        int p_mode_flags,
        Error *r_error) {
    Ref<FileAccess> ret;

    // 只读时先尝试从 PackedData 中查找
    if (!(p_mode_flags & WRITE)
            && PackedData::get_singleton()
            && !PackedData::get_singleton()->is_disabled()) {
        ret = PackedData::get_singleton()->try_open_path(p_path);

        if (ret.is_valid()) {
            if (r_error) {
                *r_error = OK;
            }

            return ret;
        }
    }

    // PCK 中没找到时再走普通文件系统
    ret = create_for_path(p_path);
    Error err = ret->open(p_path, p_mode_flags);

    if (r_error) {
        *r_error = err;
    }

    return ret;
}

// 10  通过 PCK 条目创建 FileAccessPack
// FileAccessPack 构造函数负责定位文件并处理文件级加密
FileAccessPack::FileAccessPack(
        const String &p_path,
        const PackedData::PackedFile &p_file) :
        pf(p_file),
        f(FileAccess::open(pf.pack, FileAccess::READ)) {
    if (f.is_null()) {
        return;
    }

    // pf.offset 是文件数据在 PCK 中的位置
    f->seek(pf.offset);
    off = pf.offset;

    if (pf.encrypted) {
        Ref<FileAccessEncrypted> fae;
        fae.instantiate();

        Vector<uint8_t> key;
        key.resize(32);

        for (int i = 0; i < key.size(); i++) {
            key.write[i] = script_encryption_key[i];
        }

        // 文件条目级解密同样不读取 GDEC 魔数
        Error err = fae->open_and_parse(
                f,
                key,
                FileAccessEncrypted::MODE_READ,
                false);

        if (err != OK) {
            return;
        }

        // 从此以后，f 指向解密后的明文视图
        f = fae;
        off = 0;
    }

    pos = 0;
    eof = false;
}

// 11  FileAccessEncrypted::open_and_parse() 执行实际解密
Error FileAccessEncrypted::open_and_parse(
        Ref<FileAccess> p_base,
        const Vector<uint8_t> &p_key,
        Mode p_mode,
        bool p_with_magic,
        const Vector<uint8_t> &p_iv) {
    // Godot 4.4 要求 32 字节密钥，对应 AES-256
    if (p_key.size() != 32) {
        return ERR_INVALID_PARAMETER;
    }

    if (p_mode == MODE_READ) {
        if (p_with_magic) {
            // 部分独立加密文件会带 GDEC 魔数
            uint32_t magic = p_base->get_32();

            if (magic != ENCRYPTED_HEADER_MAGIC) {
                return ERR_FILE_UNRECOGNIZED;
            }
        }

        // PCK 调用时 p_with_magic=false
        // 因此当前位置直接开始读加密头
        unsigned char expected_md5[16];
        p_base->get_buffer(expected_md5, 16);

        // 记录解密后数据的真实长度
        length = p_base->get_64();

        // 读取 AES-CFB 的 IV
        iv.resize(16);
        p_base->get_buffer(iv.ptrw(), 16);

        base = p_base->get_position();

        // 密文长度按 16 字节对齐
        uint64_t decrypt_size = length;
        if (decrypt_size % 16) {
            decrypt_size += 16 - (decrypt_size % 16);
        }

        data.resize(decrypt_size);

        uint64_t read =
                p_base->get_buffer(data.ptrw(), decrypt_size);

        if (read != decrypt_size) {
            return ERR_FILE_CORRUPT;
        }

        // 执行 AES-256-CFB 解密
        CryptoCore::AESContext ctx;
        ctx.set_encode_key(p_key.ptrw(), 256);
        ctx.decrypt_cfb(
                decrypt_size,
                iv.ptrw(),
                data.ptrw(),
                data.ptrw());

        // 去除对齐数据，恢复明文原始长度
        data.resize(length);

        // 用明文 MD5 验证密钥、数据和偏移是否正确
        unsigned char actual_md5[16];
        CryptoCore::md5(data.ptr(), data.size(), actual_md5);

        if (String::md5(actual_md5) != String::md5(expected_md5)) {
            return ERR_FILE_CORRUPT;
        }

        file = p_base;
    }

    return OK;
}

// main()
//   -> ProjectSettings::setup()
//   -> ProjectSettings::_setup()
//   -> ProjectSettings::_load_resource_pack()
//   -> PackedData::add_pack()
//   -> PackedSourcePCK::try_open_pack()

// ResourceLoader::load()
//   -> ResourceLoader::_load()
//   -> ResourceFormatLoaderGDScript::load()
//   -> GDScriptCache::get_full_script()
//   -> GDScriptCache::get_shallow_script()
//   -> GDScriptCache::get_binary_tokens()
//   -> FileAccess::open()
//   -> PackedData::try_open_path()
//   -> FileAccessPack::FileAccessPack()
//   -> PACK_FILE_ENCRYPTED
//   -> FileAccessEncrypted::open_and_parse()
```

## Extension注册与加载机制

```cpp
// https://github.com/godotengine/godot/blob/4.4/core/extension/gdextension_manager.cpp
// https://github.com/godotengine/godot/blob/4.4/core/extension/gdextension.cpp
// https://github.com/godotengine/godot/blob/4.4/core/extension/gdextension_interface.h
//
// 关键函数：
// `GDExtensionManager::load_extensions()`：读 `extension_list.cfg`，逐个调 `load_extension()`
// `GDExtensionManager::load_extension_with_loader()`：创建 `GDExtension`，调 `open_library()`
// `GDExtension::open_library()`：解析 `.gdextension` 拿 `entry_symbol`，打开 `.so`，调入口函数
// `extension_init`（入口）：收 `get_proc_address`，把 initializer 写进 `initialization` 结构
// `GDExtensionManager::initialize_extensions()`：引擎按初始化等级调每个扩展的 `initializer`
// `GDREGISTER_CLASS()`：`godot-cpp` 宏，展开成 `ClassDB::register_class<T>()`
// `classdb_register_extension_class4()`：`C` 接口，往引擎 `ClassDB::classes` 写 `ClassInfo`

// 1  加载阶段和注册阶段是两件事
// 加载：引擎打开 .so，调 entry_symbol，扩展把 initializer 交给引擎，此时类还没进 ClassDB
// 注册：引擎按初始化等级调 initializer，initializer 里往 ClassDB 写类

// 2  加载阶段，从扩展列表开始
void GDExtensionManager::load_extensions() {
    Ref<FileAccess> f = FileAccess::open(
            GDExtension::get_extension_list_config_file(),  // extension_list.cfg
            FileAccess::READ);
    while (f.is_valid() && !f->eof_reached()) {
        String path = f->get_line().strip_edges();
        if (!path.is_empty()) {
            load_extension(path);  // 每条路径指向一个 .gdextension 描述
        }
    }
}

// 3  创建 GDExtension 对象，调 open_library
GDExtensionManager::LoadStatus
GDExtensionManager::load_extension_with_loader(
        const String &p_path,
        const Ref<GDExtensionLoader> &p_loader) {
    if (gdextension_map.has(p_path)) return LOAD_STATUS_ALREADY_LOADED;

    Ref<GDExtension> extension;
    extension.instantiate();

    // 关键衔接：解析描述、打开动态库、调入口
    Error err = extension->open_library(p_path, p_loader);
    if (err != OK) return LOAD_STATUS_FAILED;

    // 入口返回后，管理器接管扩展，但类还没注册
    LoadStatus status = _load_extension_internal(extension, true);
    if (status != LOAD_STATUS_OK) return status;

    gdextension_map[p_path] = extension;  // 存进 gdextension_map
    return LOAD_STATUS_OK;
}

// 4  open_library 是加载阶段的核心
Error GDExtension::open_library(const String &p_path, const Ref<GDExtensionLoader> &p_loader) {
    // 解析 .gdextension，拿 [configuration] 的 entry_symbol 和 [libraries] 的 .so 路径
    String entry_symbol = config.get_value("configuration", "entry_symbol");

    // p_loader 按平台打开 .so，Android 是 dlopen，Windows 是 LoadLibrary
    Error err = p_loader->open_library(p_path);
    if (err != OK) return err;

    // 从 .so 里找 entry_symbol 对应的函数
    GDExtensionInitializationFunction init_func =
            (GDExtensionInitializationFunction)p_loader->get_symbol(entry_symbol);

    // 准备 initialization 结构，入口函数会往里填 initializer
    GDExtensionInitialization initialization;
    initialization.userdata = this;
    initialization.initialize = nullptr;
    initialization.deinitialize = nullptr;
    initialization.minimum_initialization_level = MODULE_INITIALIZATION_LEVEL_CORE;

    // 关键衔接：调入口函数，传 get_proc_address 和 initialization
    GDExtensionBool ret = init_func(
            &gdextension_interface_get_proc_address,  // 引擎接口查询函数
            this,                                      // library token
            &initialization);                          // 输出：扩展注册的 initializer

    if (!ret) return ERR_CANT_OPEN;

    this->initialization = initialization;  // 存起来，注册阶段用
    return OK;
}

// 5  入口函数，扩展靠 get_proc_address 按名字查所有引擎 C 接口
// 不直接链接引擎符号，避免 ABI 耦合
extern "C" GDExtensionBool GDE_EXPORT extension_init(
        GDExtensionInterfaceGetProcAddress p_get_proc_address,
        GDExtensionClassLibraryPtr p_library,
        GDExtensionInitialization *r_initialization) {
    GDExtensionBinding::InitObject init_obj(
            p_get_proc_address, p_library, r_initialization);

    init_obj.register_initializer(initialize_extension);   // 注册阶段回调
    init_obj.register_terminator(uninitialize_extension);

    // SCENE 级别时 Node 系列已经在 ClassDB 里，注册自定义 Node 才安全
    init_obj.set_minimum_library_initialization_level(
            MODULE_INITIALIZATION_LEVEL_SCENE);

    return init_obj.init();
}

// 6  注册阶段，引擎按初始化等级调 initializer
void GDExtensionManager::initialize_extensions(
        GDExtension::InitializationLevel p_level) {
    for (KeyValue<String, Ref<GDExtension>> &entry : gdextension_map) {
        entry.value->initialize_library(p_level);  // 到了扩展要求的等级就调
    }
}
// 7  initializer 里注册扩展类
void initialize_extension(ModuleInitializationLevel p_level) {
    if (p_level == MODULE_INITIALIZATION_LEVEL_SCENE) {
        GDREGISTER_CLASS(MyNode);  // 展开成 ClassDB::register_class<MyNode>()
    }
}
// 8  注册类最终走 C 接口，往 ClassDB::classes 写一条 ClassInfo
// classdb_register_extension_class4(
//     library_token, class_name, parent_class_name, creation_info)
// 后续 classdb_register_extension_class_method / _property / _signal 逐条填充
```
