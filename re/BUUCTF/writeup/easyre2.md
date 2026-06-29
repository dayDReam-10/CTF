# easyre2 Writeup

## 解题思路

没啥好说的

## 解题脚本

```cpp
#include <bits/stdc++.h>
using namespace std;

int main(){
    string ans="EmBmP5Pmn7QcPU4gLYKv5QcMmB3PWHcP5YkPq3=cT6QckkPckoRG";
    string encod1="";
    for(int i=0;i<ans.size();++i){
        if(ans[i]>='A'&&ans[i]<='Z')
            encod1 += ((ans[i]-65-3)%26+26)%26+65;
        else if(ans[i]>='a'&&ans[i]<='z')
            encod1 += ((ans[i]-97-3)%26+26)%26+97;
        else if(ans[i]>='0'&&ans[i]<='9') 
            encod1 += ((ans[i]-48-3)%10+10)%10+48;
        else
            encod1 += ans[i];
    }
    // cout << encod1 << endl;
    string ans_1="BjYjM2Mjk4NzMR1dIVHs2NzJjY0MTEzM2VhMn0=zQ3NzhhMzhlOD";
    // BjYjM2Mjk4NzM
    // R1dIVHs2NzJjY
    // 0MTEzM2VhMn0=
    // zQ3NzhhMzhlOD
    string secret="";
    string ans_2="R1dIVHs2NzJjYzQ3NzhhMzhlODBjYjM2Mjk4NzM0MTEzM2VhMn0=";
    int n2=0;
    string table="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/A";
    for(int i=0;i<ans_2.size();i+=4){
        char s1=((table.find(ans_2[i])<<2)|table.find(ans_2[i+1])>>4);
        char s2=(table.find(ans_2[i+1])<<4|table.find(ans_2[i+2])>>2);
        char s3=(table.find(ans_2[i+2])<<6|table.find(ans_2[i+3]));
        if(ans_2[i+1]=='='){    
            s2=0;
            s3=0;
        }
        else if(ans_2[i+2]=='='){
            s3=0;
            
        }
        secret += s1;
        if(ans_2[i+2] != '=') secret += s2;
        if(ans_2[i+3] != '=') secret += s3;
    }
    cout << secret << endl;
}
```

## 注意事项

`ans_2` 是分块换位的结果，我换了。

## Flag

> GWHT{672cc4778a38e80cb362987341133ea2}
