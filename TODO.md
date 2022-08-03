# TODO

* [ ] Adding PDO Receive in UI and view it will crash it. *2022-08-03*

* [ ] Add 3x 0x1400 PDO Receive in jsontest.od. Needed to verify NARRAY
      *2022-08-03*

* [ ] Add info in gen_cfile.py to indicate which tool that generated the output

* [ ] How to add more than one parameter for NVAR, NARRAY and NRECORD from UI?

* [ ] Crash on GUI: new slave -> view server SDO parameter

* [ ] Save as in editor doesn't set the filename. *2022-08-02*

* [ ] Slave created in editor crash on save as json. "While processing index
      0x1401 (5121): Missing mapping". *2022-08-02*

# Resolved

* [X] Crash on GUI: new master -> custom profile -> save json
* [X] Fix issue with 'incr', 'nbmax' and 'group' found in some OD
* [X] Add version info in json od to ensure we are not forward compatible?
