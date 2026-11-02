import array, idc, ida_bytes, idautils, ida_funcs
P = {'GDPC':0x43504447,'GDSC':0x43534447,'GDEC':0x43454447,'RSRC':0x43525352,'ECFG':0x47464345}
def D(e):
    try: return idc.GetDisasm(e)
    except: return idc.generate_disasm_line(e,0)
for s in idautils.Segments():
    if not (idc.get_segm_attr(s,idc.SEGATTR_PERM) & 1): continue
    b = ida_bytes.get_bytes(s, idc.get_segm_end(s)-s) or b''
    a = array.array('I'); a.frombytes(b[:len(b)//4*4])
    m = []
    for i,w in enumerate(a):
        op = w & 0xFF800000
        if op not in (0x52800000,0x72800000,0xD2800000,0xF2800000): continue
        hw = (w>>21)&3
        if op in (0x52800000,0x72800000) and hw>1: continue
        m.append((i, w&0x1F, op in (0x52800000,0xD2800000), hw, (w>>5)&0xFFFF))
    by = {}
    for x in m: by.setdefault(x[1],[]).append(x)
    for rd,L in by.items():
        for k in range(len(L)):
            i0,_,z0,h0,v0 = L[k]
            if not z0: continue
            val = v0<<(16*h0); seq=[i0]; p=i0
            for j in range(k+1, len(L)):
                i1,_,z1,h1,v1 = L[j]
                if z1 or i1-p>6: break
                if i1-p>1 and any((a[q]&0x1F)==rd for q in range(p+1,i1)): break
                val = (val & ~(0xFFFF<<(16*h1))) | (v1<<(16*h1)); seq.append(i1); p=i1
                for n,t in P.items():
                    if (val & 0xFFFFFFFF) == t:
                        ea = s + i0*4
                        print('0x%X  %s = 0x%08X  %s' % (ea, n, t, ida_funcs.get_func_name(ea) or ''))
                        for q in seq: print('    0x%X  %s' % (s+q*4, D(s+q*4)))