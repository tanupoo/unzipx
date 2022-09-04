#!/usr/bin/env python

try:
    import pyzipper as zipfile
    import pyzipper as zipfile
    from pyzipper.zipfile import _check_compression, BadZipFile
    from pyzipper import AESZipFile as ZipFile
except ModuleNotFoundError:
    import zipfile
    from zipfile import _check_compression, BadZipFile
    from zipfile import ZipFile as ZipFile

import argparse
from os import makedirs
from os import path as ospath
import unicodedata
import re

def is_target_file(n, filename):
    """
    evaluating in below order.
    1. if the number of the filename is matched with n.
    2. if the filename is not matched with a regex in opt.excluding_files.
    3. if the filename is matched with a regex in opt.ex_files.
    4. if extract_file_number_list is empty or None.
    """
    if n in extract_file_number_list:
        return True
    for regex in opt.excluding_files:
        if re.match(regex, filename):
            return False
    for regex in opt.ex_files:
        if re.match(regex, filename):
            return True
    if not extract_file_number_list:
        return True
    return False

def do_extract(z, zi, dname, fpath):
    # check if the zipped file can be read.
    try:
        _check_compression(zi.compress_type)
    except Exception as e:
        print(f"ERROR: {e}")
        raise
    # create directories.
    if dname is not None and opt.recursive:
        try:
            makedirs(dname, mode=511, exist_ok=False)
        except FileExistsError:
            # the directory exists.
            pass
        else:
            if not opt.quiet:
                print("{} has been created.".format(dname))
    # extract the file
    if not zi.is_dir():
        with open(fpath, "wb") as fd:
            try:
                fd.write(z.read(zi))
            except BadZipFile as e:
                if "File name in directory" in str(e):
                    pass
                # ignore this exception.
            except RuntimeError as e:
                if "password required" in str(e):
                    print(f"ERROR: password required for {fpath}")
                    exit(1)
                else:
                    raise
            except Exception as e:
                print(f"ERROR: {e}")
                raise
    if not opt.quiet:
        print("extract {} into {}".format(n, fpath))

# normalization
valid_unicode_normalize_options = ["NFC", "NFKC", "NFD", "NFKD"]

ap = argparse.ArgumentParser(
        description="unzip helper to extract non utf-8 files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("zip_file", help="specify a zipped file.")
ap.add_argument("ex_files", nargs="*",
                help="specify files (regex acceptable) to be extracted.")
ap.add_argument("--prefix", action="store", dest="prefix", default="",
                help="specify a prefix.")
ap.add_argument("-i", action="store", dest="file_number",
                help="""specify a file number or list to be extracted.
                e.g. -i 2, or -i 2,3 (1 origin)
                """)
ap.add_argument("-p", "--password", action="store", dest="password",
                help="specify the password for the zipped file.")
ap.add_argument("-x", action="store_true", dest="extract_mode",
                help="extract the contents.  default is to list the files.")
ap.add_argument("-e", action="append", dest="excluding_files", default=[],
                help="specify a file name (regex acceptable) to be ignored."
                "This option can be specified in multiple.")
ap.add_argument("-E", "--encoding", action="store", dest="filename_encoding",
                default="auto",
                help="""specify a filename encoding in the zip file.
                e.g. cp932, utf-8.  default is cp932.""")
ap.add_argument("--no-convertion", action="store_false", dest="conversion",
                help="disable to convert the filename.")
ap.add_argument("-D", "--dest-dir", action="store", dest="dest_dir",
                help="specify a directory to store the files extracted.")
ap.add_argument("-R", action="store_false", dest="recursive",
                help="""extract only the 1st level of files,
                not including the sub directories.""")
ap.add_argument("-n", "--normalize", action="store", dest="unicode_normalize",
                help=f"""specify a string for normalization of the filename.
                valid string are {valid_unicode_normalize_options}""")
ap.add_argument("-q", "--quiet", action="store_true", dest="quiet",
                help="enable quiet mode.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

# filename encoding
if opt.conversion is False:
    opt.filename_encoding = None

# make the list for extracting.
extract_file_number_list = []
if opt.file_number is None:
    # means all files.
    pass
elif isinstance(opt.file_number, int):
    extract_file_number_list = [opt.file_number]
elif isinstance(opt.file_number, str):
    extract_file_number_list = [int(_) for _ in opt.file_number.split(",")]
else:
    ap.print_help()
    exit(1)
if extract_file_number_list and not opt.extract_mode:
    print("ERROR: the -x option is required when the -i option is used.")
    exit(1)

with ZipFile(opt.zip_file) as z:
    n = 1
    file_info = []
    if opt.password:
        z.setpassword(bytes(opt.password, "ascii"))
    for zi in z.infolist():
        """
        get the filename including the path.
        Because zipfile.py converts the filename as it was cp437
        when flag_bits doesn't have utf-8 bit (0x800).
        The problem is Windows OS put the filename into the zip file
        as it is.  And, in Japan, it uses Shift_JIS (cp932) Usually.
        So, zipfile.py should converts with cp932 in that case.
        The strategy here is that:
            TBD...
        """
        if opt.filename_encoding is None:
            c_fname = zi.filename
        elif opt.filename_encoding == "auto":
            if zi.flag_bits & 0x800:
                c_fname = zi.filename
            else:
                """
                some zip software (e.g. mac) doesn't set utf-8 bit even when
                the encoding of the filename was in utf-8.
                So, firstly here try to decode cp932, then try to decode utf-8.
                """
                try:
                    c_fname = zi.filename.encode("cp437").decode("utf-8")
                except:
                    c_fname = zi.filename.encode("cp437").decode("cp932")
        else:
            """
            if flag_bits has 0x800, zipfile.py converted with utf-8.
            so, here needs to back conversion by utf-8,
            then convert it with one specified.
            if not, zipfile.py uses cp437 as well.
            """
            if zi.flag_bits & 0x800:
                c_fname = zi.filename.encode("utf-8").decode(opt.filename_encoding)
            else:
                c_fname = zi.filename.encode("cp437").decode(opt.filename_encoding)
        # normalize
        if opt.unicode_normalize:
            c_fname = unicodedata.normalize(opt.unicode_normalize,
                                                   c_fname)
        # separate the filename and the path.
        # c_fname includes both.
        # add dest_dir into the path if specified.
        if c_fname is not None:
            dname, fname = ospath.split(c_fname)
            if opt.dest_dir is not None:
                dname = ospath.join(opt.dest_dir, dname)
        else:
            raise ValueError("ERROR: c_fname is None")
        if opt.dest_dir is None and dname.startswith("/"):
            raise ValueError("ERROR: c_fname started by a slash "
                             "is not allowed. use the --dest-dir option.")
        fpath = ospath.join(dname, fname)

        if is_target_file(n, c_fname) and opt.debug:
            print(f"filename: {c_fname}")
            print(f"  compress_size : {zi.compress_size}")
            print(f"  compress_type : {zi.compress_type}")
            print(f"  comment : {zi.comment}")
            print(f"  create_system : {zi.create_system}")
            print(f"  create_version: {zi.create_version}")
            print(f"  external_attr : {zi.external_attr}")
            print(f"  extra : {zi.extra}")
            print(f"  extract_version : {zi.extract_version}")
            print(f"  flag_bits     : {zi.flag_bits}")
            print("    utf-8: {}".format("yes" if zi.flag_bits & 0x800
                                        else "no"))
            print(f"  header_offset : {zi.header_offset}")
            print(f"  internal_attr : {zi.internal_attr}")
            print(f"  zi.filename   : {zi.filename}")
            print(f"  zi.orig       : {zi.orig_filename}")
            """
            if the flag has utf-8 bit, ZipFile reads the filename as utf-8.
            otherwise, it reads as cp437.
            """
            if zi.flag_bits & 0x800:
                print("    {}".format(
                        bytes(zi.filename, encoding="utf-8")))
            else:
                print("    {}".format(
                        bytes(zi.filename, encoding="cp437")))
            print(f"  volume        : {zi.volume}")

        # check whether encrypted.
        if (zi.flag_bits & 0x1) and opt.password is None:
            # XXX how to know if the password is encoded as utf-8 or not.
            print("ERROR: password required. {} is encrypted.".format(c_fname))
            exit(1)

        if is_target_file(n, c_fname):

            # extract if needed.
            if opt.extract_mode:
                try:
                    do_extract(z, zi, dname, fpath)
                except Exception as e:
                    break

            file_info.append([str(n), str(zi.file_size), zi.date_time, fpath])
        #
        n += 1

    if not opt.extract_mode and file_info:
        max_w0 = 4
        h = [ "#", "Length", "Date", "Time", "Name" ]
        max_w1 = max([len("Length"), max([len(x[1]) for x in file_info])]) + 2
        print(f"{h[0].rjust(max_w0)} {h[1].rjust(max_w1)} {h[2].center(10)} {h[3].ljust(5)} {h[4]}")
        print(f"{'-'*max_w0} {'-'*max_w1} {'-'*10} {'-'*5} {'-'*4}")
        for x in file_info:
            date = f"{x[2][0]:04}-{x[2][1]:02}-{x[2][2]:02}"
            time = f"{x[2][3]:02}:{x[2][4]:02}"
            print(f"{x[0].rjust(max_w0)} {x[1].rjust(max_w1)} {date} {time} {x[3]}")
