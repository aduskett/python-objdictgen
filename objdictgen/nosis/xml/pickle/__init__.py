from __future__ import absolute_import
"""Store Python objects to (pickle-like) XML Documents

Please see the information at gnosis.xml.pickle.doc for
explanation of usage, design, license, and other details
"""
from ._pickle import \
     XML_Pickler, XMLPicklingError, XMLUnpicklingError, \
     dump, dumps, load, loads

from .util import \
     get_class_from_store, add_class_to_store, remove_class_from_store

from .ext import *
