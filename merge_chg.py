#!/usr/bin/python

### merge_chg.py v0.1.0
### Viktor Drobot, 2019
##
## Tool for easy merging of charges calculated on REDS charge derivation server
## into AMBER prep file.
## Updated prep could be used for system preparation in tleap utility.

""" Main merge_chg script """
import argparse
import sys


# parse command line arguments
parser = argparse.ArgumentParser(description="Merge charges from REDS output into AMBER prep file")
parser.add_argument("mol2",
                    help="Output file from REDS job (in Sybyl mol2 format)")
parser.add_argument("prep",
                    help="AMBER prep file")
parser.add_argument("-O",
                    help="Overwrite source prep file, otherwise just print result on screen",
                    action="store_true")
cmdline_args = vars(parser.parse_args())

f_mol2 = cmdline_args["mol2"]
f_prep = cmdline_args["prep"]
out_ow = cmdline_args["O"]


# read the whole files
with open(f_mol2, "r") as fh_mol2:
    fs_mol2 = fh_mol2.readlines()

with open(f_prep, "r") as fh_prep:
    fs_prep = fh_prep.readlines()


# count total atom number and create index for further quick replacement
# in REDS mol2 atom count info is stored at line 7, column 1
a_cnt = int(fs_mol2[6].split()[0])
a_idx = []

# atom entries in AMBER prep start at line 11; atom name is at column 2
for i in range(10, 10 + a_cnt):
    a_idx.append({"idx": i, "name": fs_prep[i].split()[1]})

# atom entries in REDS mol2 start at line 11 too;
# atom name is at column 2 and atom charge is at column 9
for i in range(10, 10 + a_cnt):
    a_name = fs_mol2[i].split()[1]
    a_chg = fs_mol2[i].split()[8]

    # reformat atom charge to conform with AMBER prep style: [ -]\d.\d\d\d\d00
    if a_chg[0] != '-':
        a_chg = " {}00".format(a_chg)
    else:
        a_chg = "{}00".format(a_chg)

    # store new charge
    next(a for a in a_idx if a["name"] == a_name)["chg"] = a_chg


# perform index-based replacement
for a in a_idx:
    prep_s = fs_prep[a["idx"]]
    # charge entry spans from characters 64 to 72 inclusive (9 characters total)
    fs_prep[a["idx"]] = prep_s[:63] + a["chg"] + prep_s[72:]


# save result
if out_ow:
    with open(f_prep, "w") as fh_out:
        fh_out.writelines(fs_prep)
else:
    for l in fs_prep:
        print(l, end='')


sys.exit(0)
