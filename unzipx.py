#!/usr/bin/env python

import zipfile
import argparse
from os import makedirs
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

def do_extract(zi, path):
    # create directories.
    if path is not None and opt.recursive:
        try:
            makedirs(path, mode=511, exist_ok=False)
        except FileExistsError:
            pass
        else:
            if opt.verbose:
                print("{} has been created.".format(path))
    # extract the file
    if not zi.is_dir():
        with open(filename, "wb") as fd:
            try:
                fd.write(z.read(zi))
            except Exception as e:
                if "password required" in str(e):
                    print(f"ERROR: password required for {filename}")
                    exit(1)
                else:
                    print(e)
    if opt.verbose:
        print("extract {} into {}".format(n, filename))

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
ap.add_argument("-D", action="store_false", dest="enable_conversion",
                help="disable to convert the filename.")
ap.add_argument("-R", action="store_false", dest="recursive",
                help="""extract only the 1st level of files,
                not including the sub directories.""")
ap.add_argument("-n", "--normalize", action="store", dest="unicode_normalize",
                help=f"""specify a string for normalization of the filename.
                valid string are {valid_unicode_normalize_options}""")
ap.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                help="enable quiet mode.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

# filename encoding
if opt.enable_conversion is False:
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

with zipfile.ZipFile(opt.zip_file) as z:
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
            filename = zi.filename
        elif opt.filename_encoding == "auto":
            if zi.flag_bits & 0x800:
                filename = zi.filename
            else:
                """
                some zip software (e.g. mac) doesn't set utf-8 bit even when
                the encoding of the filename was in utf-8.
                So, firstly here try to decode cp932, then try to decode utf-8.
                """
                try:
                    filename = zi.filename.encode("cp437").decode("utf-8")
                except:
                    filename = zi.filename.encode("cp437").decode("cp932")
        else:
            """
            if flag_bits has 0x800, zipfile.py converted with utf-8.
            so, here needs to back conversion by utf-8,
            then convert it with one specified.
            if not, zipfile.py uses cp437 as well.
            """
            if zi.flag_bits & 0x800:
                filename = zi.filename.encode("utf-8").decode(opt.filename_encoding)
            else:
                filename = zi.filename.encode("cp437").decode(opt.filename_encoding)
        # normalize
        if opt.unicode_normalize:
            filename = unicodedata.normalize(opt.unicode_normalize, filename)
        # get the path and filename.
        if filename.startswith("/"):
            raise ValueError("ERROR: starting with a slash must not be allowed.")
        elif filename.find("/") > 0:
            path = filename[:filename.rindex("/")]
        else:
            path = None

        # check whether encrypted.
        if (zi.flag_bits & 0x1) and opt.password is None:
            # XXX how to know if the password is encoded as utf-8 or not.
            print("ERROR: password required. {} is encrypted.".format(filename))
            exit(1)

        if is_target_file(n, filename):

            # extract if needed.
            if opt.extract_mode:
                do_extract(zi, path)
            if opt.debug:
                print(f"filename: {filename}")
                print(f"  compress_size : {zi.compress_size}")
                print(f"  compress_type : {zi.compress_type}")
                print(f"  compress_type : {zi.comment}")
                print(f"  create_system : {zi.create_system}")
                print(f"  create_version: {zi.create_version}")
                print(f"  external_attr : {zi.external_attr}")
                print(f"  compress_type : {zi.extra}")
                print(f"  compress_type : {zi.extract_version}")
                print(f"  flag_bits     : {zi.flag_bits}")
                print("    utf-8: {}".format("yes" if zi.flag_bits & 0x800
                                            else "no"))
                print(f"  header_offset : {zi.header_offset}")
                print(f"  internal_attr : {zi.internal_attr}")
                print(f"  filename(zi)  : {zi.filename}")
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
                print(f"  orig_filename : {zi.orig_filename}")
                print(f"  volume        : {zi.volume}")
            file_info.append([str(n), str(zi.file_size), zi.date_time, filename])
            """
            if path is not None:
                for i,p in enumerate(path.split("/")):
                    if i == 0:
                        print("{:d}: ".format(n), end="")
                    elif i > 0:
                        print("  "*i, end="")
                    print(p)
                print("  "*(1+i), filename)
            else:
                print("{:d}: {}".format(n,filename))
            """
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
