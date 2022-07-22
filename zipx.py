#!/usr/bin/env python

import pyzipper as zipfile
from pyzipper import AESZipFile as ZipFile

from os.path import exists
from os import scandir, stat
from stat import S_ISDIR
import unicodedata
import shutil
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

# for _write_end_record()
import struct
ZIP64_LIMIT = (1 << 31) - 1
ZIP_FILECOUNT_LIMIT = (1 << 16) - 1

ZIP_BZIP2 = 12
ZIP_LZMA = 14
structEndArchive = b"<4s4H2LH"
stringEndArchive = b"PK\005\006"
structCentralDir = "<4s4B4HL2L5H2L"
stringCentralDir = b"PK\001\002"

# normalization
valid_unicode_normalize_options = ["NFC", "NFKC", "NFD", "NFKD"]

class ZipFileImproved(ZipFile):
    """
    zipfile.py in Python 3.8
    """
    def write(self, filename, arcname=None,
              compress_type=None, compresslevel=None,
              filename_encoding=None, unicode_normalize=None,
              debug=False):
        """Put the bytes from filename into the archive under the name
        arcname."""
        if not self.fp:
            raise ValueError(
                "Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError(
                "Can't write to ZIP archive while an open writing handle exists"
            )

        zinfo = zipfile.ZipInfo.from_file(filename, arcname)
        self.filename_encoding = filename_encoding
        self.unicode_normalize = unicode_normalize

        if zinfo.is_dir():
            zinfo.compress_size = 0
            zinfo.CRC = 0
        else:
            if compress_type is not None:
                zinfo.compress_type = compress_type
            else:
                zinfo.compress_type = self.compression

            if compresslevel is not None:
                zinfo._compresslevel = compresslevel
            else:
                zinfo._compresslevel = self.compresslevel

        if zinfo.is_dir():
            with self._lock:
                if self._seekable:
                    self.fp.seek(self.start_dir)
                zinfo.header_offset = self.fp.tell()  # Start of header bytes
                if zinfo.compress_type == ZIP_LZMA:
                # Compressed data includes an end-of-stream (EOS) marker
                    zinfo.flag_bits |= 0x02

                self._writecheck(zinfo)
                self._didModify = True

                self.filelist.append(zinfo)
                self.NameToInfo[zinfo.filename] = zinfo
                self.fp.write(zinfo.FileHeader(False))
                self.start_dir = self.fp.tell()
        else:
            with open(filename, "rb") as src, self.open(zinfo, 'w') as dest:
                shutil.copyfileobj(src, dest, 1024*8)

    def _write_end_record(self):
        for zinfo in self.filelist:         # write central directory
            dt = zinfo.date_time
            dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
            dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
            extra = []
            if zinfo.file_size > ZIP64_LIMIT \
               or zinfo.compress_size > ZIP64_LIMIT:
                extra.append(zinfo.file_size)
                extra.append(zinfo.compress_size)
                file_size = 0xffffffff
                compress_size = 0xffffffff
            else:
                file_size = zinfo.file_size
                compress_size = zinfo.compress_size

            if zinfo.header_offset > ZIP64_LIMIT:
                extra.append(zinfo.header_offset)
                header_offset = 0xffffffff
            else:
                header_offset = zinfo.header_offset

            extra_data = zinfo.extra
            min_version = 0
            if extra:
                # Append a ZIP64 field to the extra's
                extra_data = _strip_extra(extra_data, (1,))
                extra_data = struct.pack(
                    '<HH' + 'Q'*len(extra),
                    1, 8*len(extra), *extra) + extra_data

                min_version = ZIP64_VERSION

            if zinfo.compress_type == ZIP_BZIP2:
                min_version = max(BZIP2_VERSION, min_version)
            elif zinfo.compress_type == ZIP_LZMA:
                min_version = max(LZMA_VERSION, min_version)

            extract_version = max(min_version, zinfo.extract_version)
            create_version = max(min_version, zinfo.create_version)
            try:
                # no need, converted before.
                filename = self._encodeFilenameFlags(zinfo)
                centdir = struct.pack(structCentralDir,
                                      stringCentralDir, create_version,
                                      zinfo.create_system, extract_version, zinfo.reserved,
                                      zinfo.flag_bits, zinfo.compress_type, dostime, dosdate,
                                      zinfo.CRC, compress_size, file_size,
                                      len(filename), len(extra_data), len(zinfo.comment),
                                      0, zinfo.internal_attr, zinfo.external_attr,
                                      header_offset)
                print(f"zipped: {zinfo.filename}")
            except DeprecationWarning:
                print((structCentralDir, stringCentralDir, create_version,
                       zinfo.create_system, extract_version, zinfo.reserved,
                       zinfo.flag_bits, zinfo.compress_type, dostime, dosdate,
                       zinfo.CRC, compress_size, file_size,
                       len(zinfo.filename), len(extra_data), len(zinfo.comment),
                       0, zinfo.internal_attr, zinfo.external_attr,
                       header_offset), file=sys.stderr)
                raise
            self.fp.write(centdir)
            self.fp.write(filename)
            self.fp.write(extra_data)
            self.fp.write(zinfo.comment)

        pos2 = self.fp.tell()
        # Write end-of-zip-archive record
        centDirCount = len(self.filelist)
        centDirSize = pos2 - self.start_dir
        centDirOffset = self.start_dir
        requires_zip64 = None
        if centDirCount > ZIP_FILECOUNT_LIMIT:
            requires_zip64 = "Files count"
        elif centDirOffset > ZIP64_LIMIT:
            requires_zip64 = "Central directory offset"
        elif centDirSize > ZIP64_LIMIT:
            requires_zip64 = "Central directory size"
        if requires_zip64:
            # Need to write the ZIP64 end-of-archive records
            if not self._allowZip64:
                raise LargeZipFile(requires_zip64 +
                                   " would require ZIP64 extensions")
            zip64endrec = struct.pack(
                structEndArchive64, stringEndArchive64,
                44, 45, 45, 0, 0, centDirCount, centDirCount,
                centDirSize, centDirOffset)
            self.fp.write(zip64endrec)

            zip64locrec = struct.pack(
                structEndArchive64Locator,
                stringEndArchive64Locator, 0, pos2, 1)
            self.fp.write(zip64locrec)
            centDirCount = min(centDirCount, 0xFFFF)
            centDirSize = min(centDirSize, 0xFFFFFFFF)
            centDirOffset = min(centDirOffset, 0xFFFFFFFF)

        endrec = struct.pack(structEndArchive, stringEndArchive,
                             0, 0, centDirCount, centDirCount,
                             centDirSize, centDirOffset, len(self._comment))
        self.fp.write(endrec)
        self.fp.write(self._comment)
        self.fp.flush()

    def _encodeFilenameFlags(self, zinfo):
        # last resort.
        filename_zipped = zinfo.filename

        # unicode normalization, overwrite the filename passed.
        if self.unicode_normalize in valid_unicode_normalize_options:
            filename_zipped = unicodedata.normalize(self.unicode_normalize,
                                                    zinfo.filename)
        elif self.unicode_normalize is not None:
            raise ValueError(
                    f"unicode_normalize must be either None, {valid_unicode_normalize_options}")

        # encoding the filename.
        if self.filename_encoding is None:
            filename_zipped = filename_zipped.encode("ascii")
        elif self.filename_encoding.lower() == "cp932":
            filename_zipped = filename_zipped.encode("cp932")
        elif self.filename_encoding.lower() == "utf-8":
            filename_zipped = filename_zipped.encode("utf-8")
            zinfo.flag_bits |= 0x800   # zipped in utf-8
        else:
            raise ValueError(
                    f"""filename_encoding must be either None, cp932,
                    or utf-8, but {self.filename_encoding}""")
        return filename_zipped

def walkdir(filename, zfd):
    # check if the file is a directory or not.
    mode = stat(filename).st_mode
    if not S_ISDIR(mode):
        zfd.write(filename, filename_encoding=opt.filename_encoding,
                  unicode_normalize=opt.unicode_normalize)
        return

    # file is a directory
    with scandir(filename) as fd:
        for entry in fd:
            #print("ent: {:s}/{:s}".format(filename, entry.name))
            if entry.name.startswith(".."):
                continue
            walkdir(entry.path, zfd)

ap = ArgumentParser(
        description="zip and compress the files named a utf-8 filename.",
        formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("zip_file", help="specify a zip file.")
ap.add_argument("files", nargs="+", help="specify files to be zipped.")
ap.add_argument("-p", "--password", action="store", dest="password",
                help="specify the password for the zipped file.")
ap.add_argument("-e", "--encoding", action="store", dest="filename_encoding",
                default="cp932",
                help="specify a filename encoding.  e.g. cp932, utf-8.")
ap.add_argument("-C", action="store_false", dest="enable_conversion",
                help="disable to convert the filename.")
ap.add_argument("-n", "--normalize", action="store", dest="unicode_normalize",
                help=f"""specify a string for normalization of the filename.
                valid string are {valid_unicode_normalize_options}""")
ap.add_argument("-F", action="store_true", dest="overwrite",
                help="specity to overwrite the zip file even if exists.")
ap.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                help="enable quiet mode.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

# filename encoding
if opt.enable_conversion is False:
    opt.filename_encoding = None

extract_file_list = None

# check if the file exists.
if exists(opt.zip_file) and not opt.overwrite:
    zip_mode = "a"
else:
    zip_mode = "w"

with ZipFileImproved(opt.zip_file, zip_mode) as z:
    if opt.password:
        z.setpassword(bytes(opt.password, "ascii"))
    for filename in opt.files:
        walkdir(filename, z)

