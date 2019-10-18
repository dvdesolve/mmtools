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
