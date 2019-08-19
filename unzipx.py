#!/usr/bin/env python

import zipfile
import argparse
from os import makedirs
import sys

ap = argparse.ArgumentParser(
        description="unzip helper to extract non utf-8 files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("zip_file", metavar="FILE", help="specify a zipped file.")
ap.add_argument("--prefix", action="store", dest="prefix", default="",
                help="specify a prefix.")
ap.add_argument("-n", action="store", dest="file_number",
                help="""specify a file number or list to be extracted.
                e.g. -n 2, or -n 2,3 (1 origin)
                """)
ap.add_argument("-p", "--password", action="store", dest="password",
                help="specify the password for the zipped file.")
ap.add_argument("-x", action="store_true", dest="extract_mode",
                help="extract the contents.  default is to list the files.")
ap.add_argument("-s", action="store_true", dest="redecode_cp932",
                help="extract the filename as cp932.")
ap.add_argument("-R", action="store_false", dest="recursive",
                help="extract only the files, not including the directories.")
ap.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                help="enable quiet mode.")
opt = ap.parse_args()

file_list = None
if opt.file_number is None:
    pass
elif isinstance(opt.file_number, int):
    file_list = [opt.file_number]
elif isinstance(opt.file_number, str):
    file_list = [int(_) for _ in opt.file_number.split(",")]
else:
    ap.print_help()
    exit(1)

n = 1
with zipfile.ZipFile(opt.zip_file) as z:
    if opt.password:
        z.setpassword(bytes(opt.password, "ascii"))
    for zi in z.infolist():
        # get the filename including the path.
        if opt.redecode_cp932:
            filename = zi.filename.encode("cp437").decode("cp932")
        else:
            filename = zi.filename
        # get the path and filename.
        if filename.startswith("/"):
            raise ValueError("ERROR: starting with a slash must not be allowed.")
        elif filename.find("/") > 0:
            path = filename[:filename.rindex("/")]
        else:
            path = None
        # check whether encrypted.
        if (zi.flag_bits & 0x1) and opt.password is None:
            print("ERROR: password required. {} is encrypted.".format(path[-1]))
            exit(1)
        # extract if needed.
        if opt.extract_mode:
            if file_list is None or n in file_list:
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
                with open(filename, "wb") as fd:
                    try:
                        fd.write(z.read(zi))
                    except Exception as e:
                        if "password required" in str(e):
                            print("ERROR: password required. {} is encrypted.".
                                  format(filename))
                            exit(1)
                        else:
                            print(e)
                if opt.verbose:
                    print("extract {} into {}".format(n, filename))
        else:
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
        #
        n += 1
