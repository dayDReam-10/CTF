#include <bits/stdc++.h>
using namespace std;
int main(){
    string table="89YdTR+PB67i0HaqGJWp4FtcL5Oufle/AVNDS3IxwzCn12mUskZjhrKoyvMXgEbQ";
    string secret="IktLx2oWUJP0aFKck0ocZF+G634e/24Go94OzrP=";
    string flag="";
    int c1,c2,c3;
    for(int i=0;i<secret.size();i+=4){
        c1 = table.find(secret[i]) | ((table.find(secret[i+1]) & 3) << 6);
        c2 = ((table.find(secret[i+1]) >> 2) & 0x0F) | ((table.find(secret[i+2]) & 0x0F) << 4);
        c3 = ((table.find(secret[i+2]) >> 4) & 0x03) | (table.find(secret[i+3]) << 2);
        
        flag += char(c1);
        flag += char(c2);
        flag += char(c3);
    }
    cout << flag << endl;
}
