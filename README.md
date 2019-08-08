
# 検証
b'\xe6\xa4\x9c\xe8\xa8\xbc'
b'\xc3\xae\xc6\x92\xc3\x85'

##

>>> b0 = "検証計画（案）"
>>> b0
'検証計画（案）'
>>> b0.encode()
b'\xe6\xa4\x9c\xe8\xa8\xbc\xe8\xa8\x88\xe7\x94\xbb\xef\xbc\x88\xe6\xa1\x88\xef\xbc\x89'

## UTF-8

% ls -1 LPWA検証計画（案）_190603.pdf | hexdump 
0000000 4c 50 57 41 e6 a4 9c e8 a8 bc e8 a8 88 e7 94 bb
0000010 ef bc 88 e6 a1 88 ef bc 89 5f 31 39 30 36 30 33
0000020 2e 70 64 66 0a
0000025

>>> b1 = bytes.fromhex("""
4c 50 57 41 e6 a4 9c e8 a8 bc e8 a8 88 e7 94 bb
ef bc 88 e6 a1 88 ef bc 89 5f 31 39 30 36 30 33
2e 70 64 66
""")
>>> len(b1)
36

>>> b1[:4]
b'LPWA'
>>> b1[25:]
b'_190603.pdf'
>>> b1[4:25]
b'\xe6\xa4\x9c\xe8\xa8\xbc\xe8\xa8\x88\xe7\x94\xbb\xef\xbc\x88\xe6\xa1\x88\xef\xbc\x89'
>>> len(b1[4:25])
21
>>> b1[4:25].decode("utf-8")
'検証計画（案）'

## encrypted

>>> b2 = bytearray(b'LPWA\xc3\xae\xc6\x92\xc3\x85\xe2\x95\xaa\xc3\xaev\xc3\xab\xc2\xb5\xc3\xbci\xc3\xaa\xe2\x94\x80\xc3\xbcj_190603.pdf')
>>> len(b2)
42

>>> b2[:4]
bytearray(b'LPWA')
>>> b2[31:]
bytearray(b'_190603.pdf')
>>> b2[4:31]
bytearray(b'\xc3\xae\xc6\x92\xc3\x85\xe2\x95\xaa\xc3\xaev\xc3\xab\xc2\xb5\xc3\xbci\xc3\xaa\xe2\x94\x80\xc3\xbcj')
>>> len(b1[4:31])
27
>>> '検証計画（案）'

## RAW

0000000 4c 50 57 41 c3 ae c6 92 c3 85 e2 95 aa c3 ae 76
0000010 c3 ab c2 b5 c3 bc 69 c3 aa e2 94 80 c3 bc 6a 5f
0000020 31 39 30 36 30 33 2e 70 64 66

>>> b3 = bytes.fromhex("""
4c 50 57 41 c3 ae c6 92 c3 85 e2 95 aa c3 ae 76
c3 ab c2 b5 c3 bc 69 c3 aa e2 94 80 c3 bc 6a 5f
31 39 30 36 30 33 2e 70 64 66
""")
>>> len(b3)
42

##

0000000 4c 50 57 41 8c 9f 8f d8 8c 76 89 e6 81 69 88 c4
0000010 81 6a 5f 31 39 30 36 30 33 2e 70 64 66 0a


