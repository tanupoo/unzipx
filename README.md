zipx and unzipx
===============

zip and unzip alternative which is more friendly with East Asian Charactor.

## Background

zipfile.py converts the filename encoding into utf-8 if the flag_bits
in zipinfo has the utf-8 bit (0x800).
It converts the filename encoding into cp437 if the flag_bits doesn't
have the utf-8 bit.

## Problem

- zip software in Windows OS (at least, 7 and 10) puts the filename
  into the zip file as it is.  And, most users in Japan usually uses
  Shift_JIS (cp932) as the filenames.

- some zip software (e.g. mac, /usr/bin/zip) doesn't set utf-8 bit
  even when the encoding of the filename is in utf-8.

- when the filename contains some combining charactors,
  you will see the collapse filename.  It happens whe you use a dum terminal.

## Strategy

So, firstly this unzipx checks the utf-8 flag in flag_bits of zipinfo.
If it sets, use the filename as it is because zipfile.py can manage
the filename conversion properly.
If it doesn't set, try to convert the filename into cp932,
(actually, it restores the filename with cp437 before the conversion.)
then, if the conversion fails, it converts into utf-8.

In other way, with the -e option, you can specify the encoding you expects.

zipx and unzipx support to normalize the filename before zip or unzip files.

## FYI

```
windows 10
OS: Shift_JIS
zip: system?
filename: Shift_JIS

mac 10.14.6
OS: UTF-8
zip: /usr/bin/zip, Info-Zip 3.0
filename: UTF-8, but no UTF-8 bit
```

