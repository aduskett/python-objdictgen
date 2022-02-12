#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of CanFestival, a library implementing CanOpen Stack.
#
# Copyright (C): Edouard TISSERANT, Francis DUPIN and Laurent BESSARD
#
# See COPYING file for copyrights details.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
# from builtins import str

import getopt
import sys
import os

from . import nodemanager as nman

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name


def usage():
    print("\nUsage of objdictgen :")
    print("\n   %s XMLFilePath CFilePath\n" % sys.argv[0])


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    for opt, _ in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()

    filein = ""
    fileout = ""
    if len(args) == 2:
        filein = args[0]
        fileout = args[1]
    else:
        usage()
        sys.exit()

    if filein != "" and fileout != "":
        manager = nman.NodeManager()
        if os.path.isfile(filein):
            print("Parsing input file")
            result = manager.OpenFileInCurrent(filein)
            if not isinstance(result, (str, unicode)):
                _ = result
            else:
                print(result)
                sys.exit(-1)
        else:
            print("%s is not a valid file!" % filein)
            sys.exit(-1)
        print("Writing output file")
        result = manager.ExportCurrentToCFile(fileout)
        if isinstance(result, (str, unicode)):
            print(result)
            sys.exit(-1)
        print("All done")


if __name__ == '__main__':
    main()
