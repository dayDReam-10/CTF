# Do_you_like_Kotone WriteUp

apk? jadx打开

## 入口

追到 MainActivity：

```java
public void onClick(View v) {
    String inputText = this.editText.getText() != null ? this.editText.getText().toString() : "";
    if (this.checker.checkFlag(inputText)) {
        Toast.makeText(this, "Correct!", 0).show();
        if (this.correctMediaPlayer != null) {
            this.correctMediaPlayer.start();
            return;
        }
        return;
    }
}
```

那就追this.checker.checkFlag(inputText)呗

## Checker

```java
package com.example.ezandroid;

import android.content.Context;

/* JADX INFO: loaded from: classes3.dex */
public class Checker {
    private final char[] table;

    public native boolean check(byte[] bArr, byte[] bArr2);

    public Checker(Context context) {
        this.table = context.getString(R.string.table).toCharArray();
    }

    static {
        System.loadLibrary("ezandroid");
    }

    public boolean checkFlag(String input) {
        return check(is_it_b64encode(input.getBytes()).getBytes(), "sekaiichikawaii".getBytes()); // 加密后是这个
    }

    public String is_it_b64encode(byte[] input) {
        StringBuilder encoded = new StringBuilder();
        for (int i = 0; i < input.length; i += 3) { // 三个一组
            int b1 = input[i];
            int b2 = i + 1 < input.length ? input[i + 1] : 0;
            int b3 = i + 2 < input.length ? input[i + 2] : 0;
            encoded.append(this.table[b1 & 63]);
            encoded.append(this.table[((b1 >> 6) | (b2 << 2)) & 63]);
            char c = '=';
            encoded.append(i + 1 < input.length ? this.table[((b2 >> 4) | (b3 << 4)) & 63] : '=');
            if (i + 2 < input.length) {
                c = this.table[(b3 >> 2) & 63];
            }
            encoded.append(c);
        }
        return encoded.toString();
    }
}
```

有几个关键啊：

1. public native boolean check(byte[] bArr, byte[] bArr2);

```java
static {
    System.loadLibrary("ezandroid");
}
```

有个native标

2.

```java
public boolean checkFlag(String input) {
    return check(is_it_b64encode(input.getBytes()).getBytes(), "sekaiichikawaii".getBytes()); // 加密后是这个
}
```

额大概是比较吧

3. 加密函数

```java
    public String is_it_b64encode(byte[] input) {
        StringBuilder encoded = new StringBuilder();
        for (int i = 0; i < input.length; i += 3) { // 三个一组
            int b1 = input[i];
            int b2 = i + 1 < input.length ? input[i + 1] : 0;
            int b3 = i + 2 < input.length ? input[i + 2] : 0;
            encoded.append(this.table[b1 & 63]);
            encoded.append(this.table[((b1 >> 6) | (b2 << 2)) & 63]);
            char c = '=';
            encoded.append(i + 1 < input.length ? this.table[((b2 >> 4) | (b3 << 4)) & 63] : '=');
            if (i + 2 < input.length) {
                c = this.table[(b3 >> 2) & 63];
            }
            encoded.append(c);
        }
        return encoded.toString();
    }
```

这显然不是base64啊，不过也挺简单的 在纸上写几个12345678看看换的位置就行了

问题在于table我们要找

## 解题步骤

额反正我是搜索table慢慢找的（当时不知道可以去strings.xml...）

总之：

```xml
<string name="table">89YdTR+PB67i0HaqGJWp4FtcL5Oufle/AVNDS3IxwzCn12mUskZjhrKoyvMXgEbQ</string>
```

这个 b64 比较好写，我们先去看 check 是啥：

```java
static {
        System.loadLibrary("ezandroid");
}
```

load 了这个，改名 zip 后找到 so，ida 打开，看见：

```c
RC4(v8, (int)ArrayLength, v9, (int)ArrayLength_3, v10);
if ( ArrayLength == 40 )
{
    for ( i = 0; i < 40; ++i )
    {
        if ( v10[i] != byte_610[i] )
        {
            v23 = 0;
            v12 = 1;
            return v23;
        }
    }
    v23 = 1;
    v12 = 1;
}
else
{
    v23 = 0;
    v12 = 1;
}
return v23;
}
```

一个RC4一个遍历对比

额没学过RC4 不过先看对比位是v10，所以v10是输出

然后比对一下看看参数位，知道ArrayLength_3是sekaiichikawaii的长度

那v8就是input转完b64的东西喽，没啥好说的，改个名字

RC4(input, (int)ArrayLength_input, cipher, (int)ArrayLength_output, output);

打开cyberchef，赛博做饭（划掉）key就是a4=sekaiichikawaii,密文在byte里面，input hex output Latin1

```text
IktLx2oWUJP0aFKck0ocZF+G634e/24Go94OzrP=
```


再反解就行