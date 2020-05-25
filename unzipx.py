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
ap.add_argument("-S", action="store_false", dest="redecode_cp932",
                help="disable to extract the filename as cp932.")
ap.add_argument("-R", action="store_false", dest="recursive",
                help="extract only the 1st level of files, not including the sub directories.")
ap.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                help="enable quiet mode.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

extract_file_list = None
if opt.file_number is None:
    # means all files.
    pass
elif isinstance(opt.file_number, int):
    extract_file_list = [opt.file_number]
elif isinstance(opt.file_number, str):
    extract_file_list = [int(_) for _ in opt.file_number.split(",")]
else:
    ap.print_help()
    exit(1)

with zipfile.ZipFile(opt.zip_file) as z:
    n = 1
    file_info = []
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
            print("ERROR: password required. {} is encrypted.".format(filename))
            exit(1)
        # extract if needed.
        if opt.extract_mode:
            if extract_file_list is None or n in extract_file_list:
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
        else:
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
                print(f"  header_offset : {zi.header_offset}")
                print(f"  internal_attr : {zi.internal_attr}")
                print(f"  orig_filename : {zi.orig_filename}")
                print(f"  volume        : {zi.volume}")
            file_info.append([str(zi.file_size), zi.date_time, filename])
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
    if not opt.extract_mode:
        h = [ "Length", "Date", "Time", "Name" ]
        max_w1 = max([len(x[0]) for x in file_info]) + 1
        print(f"{h[0].rjust(max_w1)} {h[1].center(10)} {h[2].ljust(5)} {h[3]}")
        print(f"{'-'*max_w1} {'-'*10} {'-'*5} {'-'*4}")
        for x in file_info:
            date = f"{x[1][0]:04}-{x[1][1]:02}-{x[1][2]:02}"
            time = f"{x[1][3]:02}:{x[1][4]:02}"
            print(f"{x[0].rjust(max_w1)} {date} {time} {x[2]}")
