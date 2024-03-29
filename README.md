zipx and unzipx
===============

zip and unzip alternative which is more friendly with East Asian Charactor,
and new encryption algorithms.

## Installation

Not required, but recommended to support newer compression.

```
pip install pyzipper
```

## Background: Problem

- zipfile.py is a nice tool.  However, it converts the encoding of the filename
  into cp437 if the utf-8 bit (0x800) in the flag_bits of zipinfo is not set.

- zip software in Windows OS (at least, 7 and 10) puts the filename
  into the zip file as it is.  It doesn't set the utf-8 bit even if
  it is encoded by UTF-8.

- Most users in Japan usually uses Shift_JIS (cp932) as the filenames.
  Mac users will see a corrupted filename when they decode such a zip file.

- some zip software (e.g. mac, /usr/bin/zip) doesn't set utf-8 bit
  even when the encoding of the filename is in utf-8.
  Windows users will see a corrupted filename when they decode such a zip file.

- Mac Archive Utility doesn't handle the filename conversion as well.

- when the filename contains some combining charactors of Unicode,
  you will see the corrupted filename.  It happens when you use a dum terminal.

- Another problem is the version of PKZIP.  Several versions exist.  Some
  tools don't some recent versions.  For example, Mac native unzip
  doesn't support some encryption algorithms such as AES256.  In this case,
  you see the message like "need PK compat. v5.1 (can do v4.5)".

- Even betwen Windows OS, a user can't decrypt a zip file.
  That is because the embeded unzip utility (Zipcrypto) doesn't support AES256.
  7z or lhaplus could decrypt such file.

## Strategy

I do want a single solution to solve above problems.

So, firstly this unzipx checks the utf-8 flag in flag_bits of zipinfo.
If it sets, use the filename as it is because zipfile.py can manage
the filename conversion properly.
If it doesn't set, try to convert the filename into cp932,
(actually, it restores the filename with cp437 before the conversion.)
then, if the conversion fails, it converts into utf-8.

In other way, with the -e option, you can specify the encoding you expects.

zipx and unzipx support to normalize the filename before zip or unzip files.

To support new Encryption algorithms, unzipx tries to use pyzipper if available.

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

