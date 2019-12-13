# mmtools
Set of different tools that may be useful in molecular modeling

## Charge derivation

### `merge_chg.py`
Merges charges from [REDS](http://upjv.q4md-forcefieldtools.org/REDServer-Development/) `mol2` output file (Sybyl mol2 format) into [AMBER `prep`](http://ambermd.org/doc/prep.html) file: just an easy way to replace mediocre semi-empirical charges calculated with `antechamber` utility with high-quality RESP charges.

#### Usage
```
./merge_chg.py [-h] [-O] mol2 prep
```

- `mol2` -- output file from REDS job with RESP charges
- `prep` -- AMBER `prep` file
- `-O` -- if specified source `prep` file will be overwritten; otherwise output will be printed on screen
- `-h` -- print help

## Topology management

### `rst_reorder.py`
Reorders atoms in [AMBER restart](https://ambermd.org/FileFormats.php#restart) file that bound to the old topology to be consistent with new topology. Common use cases: after QM/MM stages during molecular dynamics (MD) one may want to continue classical MD simulations but it's impossible to do without re-creating topology. But even if number of atoms remains the same there is no native utility in AmberTools package to save the velocities and not only the coordinates. Using these tool allows you to explore and simulate the whole multistep catalytic pathways without regenerating system, energy minimization, heating etc...

So to perform reordering properly and save velocities you should do the following:
1. Get your restart file with velocity information (e. g., **last.rst**).
2. Using old topology (e. g., **last.prmtop**) and restart file (**last.rst**) generate intermediate PDB (e. g., **last.pdb**) with the help of `ambpdb` tool.
3. Edit your **last.pdb** and rename necessary atoms, residues to comply with desired topology (depends on your system). Don't forget to move atom entries to the corresponding places in PDB and reassign residue numbers for changed entries as well. Don't worry about *atom numbering* for now -- you can always use `pdb4amber` tool to fix it. Save final cleared PDB as **last_fixed.pdb** for example.
4. Use `tleap` and generate two systems based on **last_fixed.pdb** -- just load all necessary force fields, OFF libraries and frcmods and you're ready. You will need two systems:
  - the first system should have periodic box; use `setBox` command to create one (`centers` or `vdw` doesn't matter -- `rst_reorder.py` will care about transferring the right PBC). Save the result as **new.prmtop** and **tmp.inpcrd**
  - the second system shouldn't have any periodic box -- just load your PDB and save **tmp.prmtop** and **new.inpcrd**

   You will need these two files for next steps: **new.prmtop** and **new.inpcrd**. The reason for double system generation is that `tleap` shifts origin of your input system when PBCs are applied -- this gives us the right topology but translated coordinates. You could manually find translation vector by comparing unchanged atom positions and re-translate new coordinates back but generation of the second system seems to be much easier.

5. Run `rst_reorder.py` using **last.rst** and **new.inpcrd** as input files. Set tolerance for the detection of atom swapping (0.004 angstroms is pretty good). Save reordered system to **new.rst**
6. ???????
7. PROFIT! You can use now **new.prmtop** and **new.rst** as starting point for next MD runs. Atom positions and velocities are conserved but topology is regenerated so you should be fine.

#### Usage
```
./reorder.py [-h] old new tol
```

- `old` -- restart file for old topology
- `new` -- restart file for new topology
- `tol` -- distance tolerance for atom mapping (in units of restart file, usually angstroms)
- `-h` -- print help
