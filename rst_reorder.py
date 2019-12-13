#!/usr/bin/python

### rst_reorder.py v0.1.0
### Viktor Drobot, 2019
##
## tool for re-ordering AMBER restart file with old topology to conform to atom arrangement with new topology
## saves periodic box and velocity info, if any presented in old restart file



### imports ###
import argparse
from enum import Enum
from math import sqrt
import sys



### restart file class ###
class rstfile:
    # file type
    class rstfile_type(Enum):
        NOPBC_NOVEL = 0
        NOPBC_VEL   = 1
        PBC_NOVEL   = 2
        PBC_VEL     = 3


    # atom definition
    class rstfile_atom:
        def __init__(self, x = None, y = None, z = None, vx = None, vy = None, vz = None):
            self.x = x
            self.y = y
            self.z = z
            self.vx = vx
            self.vy = vy
            self.vz = vz
            self.maps_to = None


    # custom exceptions
    class rstfile_error(Exception):
        def __init__(self, filename, text):
            self.fname = filename
            self.msg = text


    # constructor
    def __init__(self, filename):
        self.valid = False
        self.type = None
        self.fname = filename
        self.header = None
        self.natoms = None
        self.time = None
        self.with_vel = False
        self.pbc = {}
        self.atoms = []

    # parser
    def parse(self):
        with open(self.fname, "r") as fh:
            # get header - the only string in the whole file
            self.header = fh.readline()

            if not self.header:
                raise self.rstfile_error(self.fname, "no header found")

            # get number of atoms and (possibly) time
            line = fh.readline()

            if not line:
                raise self.rstfile_error(self.fname, "no atoms number and/or time info")

            line_data = line.split()

            if len(line_data) == 1:
                self.natoms = int(line_data[0])
            elif len(line_data) == 2:
                self.natoms = int(line_data[0])
                self.time = float(line_data[1])
            else:
                raise self.rstfile_error(self.fname, "malformed NATOMS,TIME line")

            # read and store atom coordinates
            last_is_single = True if (self.natoms % 2) == 1 else False # whether last line for coordinates/velocities contain only single atom entry
            n_data_lines = (self.natoms // 2) + (self.natoms % 2) # number of data lines that we should read

            for i in range(0, n_data_lines):
                line = fh.readline()

                if not line:
                    raise self.rstfile_error(self.fname, "premature end of file")

                line_data = line.split()

                if (len(line_data) != 3) and (len(line_data) != 6):
                    raise self.rstfile_error(self.fname, "malformed coordinates line #{}".format(i + 3))

                self.atoms.append(self.rstfile_atom(float(line_data[0]), float(line_data[1]), float(line_data[2])))

                if (i < (n_data_lines - 1)) or ((i == (n_data_lines - 1) and not last_is_single)):
                    self.atoms.append(self.rstfile_atom(float(line_data[3]), float(line_data[4]), float(line_data[5])))

            # store current file position for further re-reading
            offset = fh.tell()

            # determine file type
            succ_read = 0

            while True:
                line = fh.readline()

                if not line:
                    break

                succ_read += 1

            if succ_read == 0:
                self.type = self.rstfile_type.NOPBC_NOVEL
                self.valid = True
                return
            elif succ_read == 1:
                self.type = self.rstfile_type.PBC_NOVEL
            elif succ_read == (n_data_lines + 1):
                self.type = self.rstfile_type.PBC_VEL
            elif succ_read == n_data_lines:
                self.type = self.rstfile_type.NOPBC_VEL
            else:
                raise self.rstfile_error(self.fname, "can't determine file type")

            # jump back
            fh.seek(offset)

            # read and store velocities (if any)
            if (self.type == self.rstfile_type.NOPBC_VEL) or (self.type == self.rstfile_type.PBC_VEL):
                for i in range(0, n_data_lines):
                    line = fh.readline()

                    line_data = line.split()

                    if (len(line_data) != 3) and (len(line_data) != 6):
                        raise self.rstfile_error(self.fname, "malformed velocities line #{}".format(i + 3))

                    self.atoms[2 * i].vx = float(line_data[0])
                    self.atoms[2 * i].vy = float(line_data[1])
                    self.atoms[2 * i].vz = float(line_data[2])

                    if (i < (n_data_lines - 1)) or ((i == (n_data_lines - 1) and not last_is_single)):
                        self.atoms[2 * i + 1].vx = float(line_data[3])
                        self.atoms[2 * i + 1].vy = float(line_data[4])
                        self.atoms[2 * i + 1].vz = float(line_data[5])

                self.with_vel = True

            # read and store pbc (if any)
            if (self.type == self.rstfile_type.PBC_NOVEL) or (self.type == self.rstfile_type.PBC_VEL):
                line = fh.readline()
                line_data = line.split()

                if len(line_data) != 6:
                    raise self.rstfile_error(self.fname, "malformed PBC line")

                self.pbc["a"] = float(line_data[0])
                self.pbc["b"] = float(line_data[1])
                self.pbc["c"] = float(line_data[2])
                self.pbc["alpha"] = float(line_data[3])
                self.pbc["beta"] = float(line_data[4])
                self.pbc["gamma"] = float(line_data[5])

            # finish reading
            self.valid = True
            return



### main program ###
## parse command line arguments
# TODO ask for output file name (optional)
parser = argparse.ArgumentParser(description = "Shuffle old-topology restart to a new-topology order")
parser.add_argument("old", help = "restart file for old topology")
parser.add_argument("new", help = "restart file for old topology")
parser.add_argument("tol", help = "tolerance of distance", type = float)
cmdline_args = vars(parser.parse_args())

old_rst = cmdline_args["old"]
new_rst = cmdline_args["new"]
tolerance = cmdline_args["tol"]


## parse both restart files
old_system = rstfile(old_rst)
new_system = rstfile(new_rst)

old_system.parse()
new_system.parse()

# check for equality in length
if old_system.natoms != new_system.natoms:
    print("[ERROR] Two restart files contain different number of atoms!", file = sys.stderr)
    sys.exit(1)


## find mappings between two systems with given tolerance
natoms = old_system.natoms
old_idx_pool = set()

for i in range(0, natoms):
    old_idx_pool.add(i)

for i in range(0, natoms):
    new_atom = new_system.atoms[i]

    match_found = False

    for j in old_idx_pool:
        old_atom = old_system.atoms[j]

        # TODO add support for translation disposition
        if sqrt((old_atom.x - new_atom.x)**2 + (old_atom.y - new_atom.y)**2 + (old_atom.z - new_atom.z)**2) <= tolerance:
            new_atom.maps_to = j
            match_found = True
            old_idx_pool.remove(j)

            break

    if not match_found:
        print("[ERROR] No match found for atom #{} in {}!".format(i + 1, new_rst), file = sys.stderr)
        sys.exit(1)


## save reordered restart file (conforming to the AMBER restart file formatting)
# write metadata
print("%-.80s" % (old_system.header.rstrip()))
print("%5d" % (natoms), end = '')

if old_system.time:
    print("%15.7E" % (old_system.time))
else:
    print('\n', end = '')

# write coordinates
for i in range(0, natoms):
    atom = old_system.atoms[new_system.atoms[i].maps_to]
    print("%12.7f%12.7f%12.7f" % (atom.x, atom.y, atom.z), end = ('' if (i % 2) == 0 else '\n'))

if (i % 2) == 0:
    print('\n', end = '')

# write velocities (if any)
if old_system.with_vel:
    for i in range(0, natoms):
        atom = old_system.atoms[new_system.atoms[i].maps_to]
        print("%12.7f%12.7f%12.7f" % (atom.vx, atom.vy, atom.vz), end = ('' if (i % 2) == 0 else '\n'))

    if (i % 2) == 0:
        print('\n', end = '')

# write pbc info (if any)
if old_system.pbc:
    print("%12.7f%12.7f%12.7f%12.7f%12.7f%12.7f" % (old_system.pbc["a"], old_system.pbc["b"], old_system.pbc["c"], old_system.pbc["alpha"], old_system.pbc["beta"], old_system.pbc["gamma"])) 


sys.exit(0)
