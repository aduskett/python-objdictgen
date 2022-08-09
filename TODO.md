# TODO

# Issues

* [ ] Viewing of PDO Receive in UI it will crash it. *2022-08-03*

* [ ] Add info in gen_cfile.py to indicate which tool that generated the output

* [ ] Crash on GUI: new slave -> view server SDO parameter

* [ ] Save as in editor doesn't set the filename. *2022-08-02*

# Resolved

* [X] Change `struct`, `need`, `type` to human readable variants in JSON
      format. *2022-08-03*
* [X] Index 0x160E (5646) from ResusciFamilyMasterOD.od fails with
      "Index 0x160e (5646): User parameters not empty. Programming error?"
      *2022-08-03*
* [X] Logging doesn't seem to work in py. No WARNINGS printed. *2022-08-03*
* [X] Slave created in editor crash on save as json. "While processing index
      0x1401 (5121): Missing mapping". *2022-08-02*
* [-] How to add more than one parameter for NVAR, NARRAY and NRECORD from UI?
* [X] Add 3x 0x1400 PDO Receive in jsontest.od. Needed to verify NARRAY
      *2022-08-03*
* [X] Running `odg diff jsontest.od jsontest.json` doesn't compare equal
      *2022-08-03*
* [X] `odg diff` doesnt return error code even if difference. *2022-08-03*
* [X] Convert `odg conversion jsontest.od jsontest.json` fails with "Uexpected
      parameters 'nbmin' in mapping values". *2022-08-03*
* [X] `odg list jsontest.od` fails on index 0x1600. *2022-08-03*
* [X] Crash on GUI: new master -> custom profile -> save json
* [X] Fix issue with 'incr', 'nbmax' and 'group' found in some OD
* [X] Add version info in json od to ensure we are not forward compatible?
