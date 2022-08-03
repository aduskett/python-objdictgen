from __future__ import print_function
from __future__ import absolute_import
from builtins import object

import sys
from io import StringIO
from collections import OrderedDict
from xml.dom import minidom
from past.builtins import long
from future.utils import raise_from

from .xtoy import (
    aton, ntoa,
    unsafe_string, unsafe_content,
    safe_string, safe_content,
)

if sys.version_info[0] >= 3:
    unicode = str  # pylint: disable=invalid-name
    ODict = dict
else:
    ODict = OrderedDict


class _EmptyClass(object):
    """ Do-nohting empty class """


TYPE_IN_BODY = {
    int: 0,
    long: 0,
    float: 0,
    complex: 0,
    str: 0,
}

if sys.version_info[0] < 3:
    # our unicode vs. "regular string" scheme relies on unicode
    # strings only being in the body, so this is hardcoded.
    TYPE_IN_BODY[unicode] = 1
else:
    # py3 doesn't have unicode, and unicode here is str. This implies that
    # on py3 all strings will be added as body elements instead of tag value="..."
    TYPE_IN_BODY[unicode] = 1


def getInBody(typename):
    return TYPE_IN_BODY.get(typename) or 0


# Maintain list of object identities for multiple and cyclical references
# (also to keep temporary objects alive)
VISITED = {}


# entry point expected by XML_Pickle
def thing_from_dom(filehandle):
    global VISITED
    VISITED = {}
    return _thing_from_dom(minidom.parse(filehandle), None)


def _save_obj_with_id(node, obj):
    objid = node.getAttribute('id')

    if len(objid):  # might be None, or empty - shouldn't use as key
        VISITED[objid] = obj


# Store the objects that can be pickled
CLASS_STORE = {}


def add_class_to_store(classname='', klass=None):
    "Put the class in the store (as 'classname'), return CLASS_STORE"
    if classname and klass:
        CLASS_STORE[classname] = klass
    return CLASS_STORE


def get_class_from_name(classname):
    """Given a classname, optional module name, return a ClassType,
    of type module.classname, obeying the PARANOIA rules."""

    klass = CLASS_STORE.get(classname, None)
    if klass:
        return klass
    raise ValueError("Cannot create class '%s'" % classname)


def obj_from_node(node):
    """Given a <PyObject> node, return an object of that type.
    __init__ is NOT called on the new object, since the caller may want
    to do some additional work first.
    """
    classname = node.getAttribute('class')
    # allow <PyObject> nodes w/out module name
    # (possibly handwritten XML, XML containing "from-air" classes,
    # or classes placed in the CLASS_STORE)
    klass = get_class_from_name(classname)
    return klass.__new__(klass)


def get_node_valuetext(node):
    "Get text from node, whether in value=, or in element body."

    # we know where the text is, based on whether there is
    # a value= attribute. ie. pickler can place it in either
    # place (based on user preference) and unpickler doesn't care

    if 'value' in node._attrs:
        # text in tag
        ttext = node.getAttribute('value')
        return unsafe_string(ttext)

    # text in body
    node.normalize()
    if node.childNodes:
        return unsafe_content(node.childNodes[0].nodeValue)
    return ''


# a multipurpose list-like object. it is nicer conceptually for us
# to pass lists around at the lower levels, yet we'd also like to be
# able to do things like write to a file without the overhead of building
# a huge list in memory first. this class handles that, yet drops in (for
# our purposes) in place of a list.
#
# (it's not based on UserList so that (a) we don't have to pull in UserList,
# and (b) it will break if someone accesses StreamWriter in an unexpected way
# rather than failing silently for some cases)
class StreamWriter(object):
    """A multipurpose stream object. Four styles:

    - write an uncompressed file
    - write a compressed file
    - create an uncompressed memory stream
    - create a compressed memory stream
    """
    def __init__(self, iohandle=None, compress=None):

        if iohandle:
            self.iohandle = iohandle
        else:
            self.iohandle = self.sio = StringIO()

        if compress == 1:  # maybe we'll add more types someday
            import gzip
            self.iohandle = gzip.GzipFile(None, 'wb', 9, self.iohandle)

    def append(self, item):
        if isinstance(item, (list, tuple)):
            item = ''.join(item)
        self.iohandle.write(item)

    def getvalue(self):
        "Returns memory stream as a single string, or None for file objs"
        if hasattr(self, 'sio'):
            if self.iohandle != self.sio:
                # if iohandle is a GzipFile, we need to close it to flush
                # remaining bits, write the CRC, etc. However, if iohandle is
                # the sio, we CAN'T close it (getvalue() wouldn't work)
                self.iohandle.close()
            return self.sio.getvalue()

        # don't raise an exception - want getvalue() unconditionally
        return None


# split off for future expansion of compression types, etc.
def StreamReader(stream):
    """stream can be either a filehandle or string, and can
    be compressed/uncompressed. Will return either a fileobj
    appropriate for reading the stream."""

    # turn strings into stream
    if isinstance(stream, (str, unicode)):
        stream = StringIO(stream)

    # determine if we have a gzipped stream by checking magic
    # number in stream header
    pos = stream.tell()
    magic = stream.read(2)
    stream.seek(pos)
    if magic == '\037\213':
        import gzip
        stream = gzip.GzipFile(None, 'rb', None, stream)

    return stream


def xmldump(iohandle=None, obj=None, binary=0, deepcopy=None, omit=None):
    "Create the XML representation as a string."
    if deepcopy is None:
        deepcopy = 0
    return _pickle_toplevel_obj(StreamWriter(iohandle, binary), obj, deepcopy, omit)


def xmlload(filehandle):
    "Load pickled object from file fh."
    return thing_from_dom(StreamReader(filehandle))


# -- support functions


def _pickle_toplevel_obj(xml_list, py_obj, deepcopy, omit=None):
    "handle the top object -- add XML header, etc."

    # Store the ref id to the pickling object (if not deepcopying)
    global VISITED
    VISITED = {}
    if not deepcopy:
        id_ = id(py_obj)
        VISITED[id_] = py_obj

    # note -- setting family="obj" lets us know that a mutator was used on
    # the object. Otherwise, it's tricky to unpickle both <PyObject ...>
    # and <.. type="PyObject" ..> with the same code. Having family="obj" makes
    # it clear that we should slurp in a 'typeless' object and unmutate it.

    # note 2 -- need to add type= to <PyObject> when using mutators.
    # this is b/c a mutated object can still have a class= and
    # module= that we need to read before unmutating (i.e. the mutator
    # mutated into a PyObject)

    famtype = ''  # unless we have to, don't add family= and type=

    klass = py_obj.__class__
    klass_tag = klass.__name__

    # Generate the XML string
    # if klass not in CLASS_STORE.values():
    module = klass.__module__.replace('objdictgen.', '')  # Workaround to be backwards compatible
    extra = '%smodule="%s" class="%s"' % (famtype, module, klass_tag)
    # else:
    #     extra = '%s class="%s"' % (famtype, klass_tag)

    xml_list.append('<?xml version="1.0"?>\n'
                    + '<!DOCTYPE PyObject SYSTEM "PyObjects.dtd">\n')

    if deepcopy:
        xml_list.append('<PyObject %s>\n' % (extra))
    elif id_ is not None:
        xml_list.append('<PyObject %s id="%s">\n' % (extra, id_))
    else:
        xml_list.append('<PyObject %s>\n' % (extra))

    pickle_instance(py_obj, xml_list, level=0, deepcopy=deepcopy, omit=omit)
    xml_list.append('</PyObject>\n')

    # returns None if xml_list is a fileobj, but caller should
    # know that (or not care)
    return xml_list.getvalue()


def pickle_instance(obj, list_, level=0, deepcopy=0, omit=None):
    """Pickle the given object into a <PyObject>

    Add XML tags to list. Level is indentation (for aesthetic reasons)
    """
    # concept: to pickle an object:
    #
    #   1. the object attributes (the "stuff")
    #
    # There is a twist to this -- instead of always putting the "stuff"
    # into a container, we can make the elements of "stuff" first-level attributes,
    # which gives a more natural-looking XML representation of the object.

    stuff = obj.__dict__

    # decide how to save the "stuff", depending on whether we need
    # to later grab it back as a single object
    if isinstance(stuff, dict):
        # don't need it as a single object - save keys/vals as
        # first-level attributes
        for key, val in stuff.items():
            if omit and key in omit:
                continue
            list_.append(_attr_tag(key, val, level, deepcopy))
    else:
        raise ValueError("'%s.__dict__' is not a dict" % (obj))


def unpickle_instance(node):
    """Take a <PyObject> or <.. type="PyObject"> DOM node and unpickle the object."""

    # we must first create an empty obj of the correct	type and place
    # it in VISITED{} (so we can handle self-refs within the object)
    pyobj = obj_from_node(node)
    _save_obj_with_id(node, pyobj)

    # slurp raw thing into a an empty object
    raw = _thing_from_dom(node, _EmptyClass())

    # code below has same ordering as pickle.py

    stuff = raw.__dict__

    # finally, decide how to get the stuff into pyobj
    if isinstance(stuff, dict):
        for k, v in stuff.items():
            setattr(pyobj, k, v)

    else:
        # subtle -- this can happen either because the class really
        # does violate the pickle protocol
        raise ValueError("Non-dict violates pickle protocol")

    return pyobj


# --- Functions to create XML output tags ---
def _attr_tag(name, thing, level=0, deepcopy=0):
    start_tag = '  ' * level + ('<attr name="%s" ' % name)
    close_tag = '  ' * level + '</attr>\n'
    return _tag_completer(start_tag, thing, close_tag, level, deepcopy)


def _item_tag(thing, level=0, deepcopy=0):
    start_tag = '  ' * level + '<item '
    close_tag = '  ' * level + '</item>\n'
    return _tag_completer(start_tag, thing, close_tag, level, deepcopy)


def _entry_tag(key, val, level=0, deepcopy=0):
    start_tag = '  ' * level + '<entry>\n'
    close_tag = '  ' * level + '</entry>\n'
    start_key = '  ' * level + '  <key '
    close_key = '  ' * level + '  </key>\n'
    key_block = _tag_completer(start_key, key, close_key, level + 1, deepcopy)
    start_val = '  ' * level + '  <val '
    close_val = '  ' * level + '  </val>\n'
    val_block = _tag_completer(start_val, val, close_val, level + 1, deepcopy)
    return start_tag + key_block + val_block + close_tag


def _tag_compound(start_tag, family_type, thing, deepcopy, extra=''):
    """Make a start tag for a compound object, handling deepcopy & refs.
    Returns (start_tag,do_copy), with do_copy indicating whether a
    copy of the data is needed.
    """
    if deepcopy:
        # don't need ids in a deepcopied file (looks neater)
        start_tag = start_tag + '%s %s>\n' % (family_type, extra)
        return (start_tag, 1)

    if VISITED.get(id(thing)):
        start_tag = start_tag + '%s refid="%s" />\n' % (family_type, id(thing))
        return (start_tag, 0)

    start_tag = start_tag + '%s id="%s" %s>\n' % (family_type, id(thing), extra)
    return (start_tag, 1)


#
# This doesn't fit in any one place particularly well, but
# it needs to be documented somewhere. The following are the family
# types currently defined:
#
#   obj - thing with attributes and possibly coredata
#
#   uniq - unique thing, its type gives its value, and vice versa
#
#   map - thing that maps objects to other objects
#
#   seq - thing that holds a series of objects
#
#         Note - Py2.3 maybe the new 'Set' type should go here?
#
#   atom - non-unique thing without attributes (e.g. only coredata)
#
#   lang - thing that likely has meaning only in the
#          host language (functions, classes).
#
#          [Note that in Gnosis-1.0.6 and earlier, these were
#           mistakenly placed under 'uniq'. Those encodings are
#           still accepted by the parsers for compatibility.]
#

def _family_type(family, typename, mtype, mextra):
    """Create a type= string for an object, including family= if necessary.
    typename is the builtin type, mtype is the mutated type (or None for
    non-mutants). mextra is mutant-specific data, or None."""
    if mtype is None:
        # family tags are technically only necessary for mutated types.
        # we can intuit family for builtin types.
        return 'type="%s"' % typename

    if mtype and len(mtype):
        if mextra:
            mextra = 'extra="%s"' % mextra
        else:
            mextra = ''
        return 'family="%s" type="%s" %s' % (family, mtype, mextra)
    return 'family="%s" type="%s"' % (family, typename)


def _fix_family(family, typename):
    """
    If family is None or empty, guess family based on typename.
    (We can only guess for builtins, of course.)
    """
    if family and len(family):
        return family  # sometimes it's None, sometimes it's empty ...

    if typename == 'None':
        return 'none'
    if typename == 'dict':
        return 'map'
    if typename == 'list':
        return 'seq'
    if typename == 'tuple':
        return 'seq'
    if typename == 'numeric':
        return 'atom'
    if typename == 'string':
        return 'atom'
    if typename == 'PyObject':
        return 'obj'
    if typename == 'function':
        return 'lang'
    if typename == 'class':
        return 'lang'
    if typename == 'True':
        return 'uniq'
    if typename == 'False':
        return 'uniq'
    raise ValueError("family= must be given for unknown type '%s'" % typename)


def _tag_completer(start_tag, orig_thing, close_tag, level, deepcopy):
    tag_body = []

    (mtag, thing, in_body, mextra) = (None, orig_thing, getInBody(type(orig_thing)), None)

    if thing is None:
        start_tag = start_tag + "%s />\n" % (_family_type('none', 'None', None, None))
        close_tag = ''
    # bool cannot be used as a base class (see sanity check above) so if thing
    # is a bool it will always be BooleanType, and either True or False
    elif isinstance(thing, bool):
        if thing is True:
            typestr = 'True'
        else:  # must be False
            typestr = 'False'

        if in_body:
            start_tag = start_tag + '%s>%s' % (
                _family_type('uniq', typestr, mtag, mextra), '')
            close_tag = close_tag.lstrip()
        else:
            start_tag = start_tag + '%s value="%s" />\n' % (
                _family_type('uniq', typestr, mtag, mextra), '')
            close_tag = ''
    elif isinstance(thing, (int, long, float, complex)):
        # thing_str = repr(thing)
        thing_str = ntoa(thing)

        if in_body:
            # we don't call safe_content() here since numerics won't
            # contain special XML chars.
            # the unpickler can either call unsafe_content() or not,
            # it won't matter
            start_tag = start_tag + '%s>%s' % (
                _family_type('atom', 'numeric', mtag, mextra), thing_str)
            close_tag = close_tag.lstrip()
        else:
            start_tag = start_tag + '%s value="%s" />\n' % (
                _family_type('atom', 'numeric', mtag, mextra), thing_str)
            close_tag = ''
    elif isinstance(thing, (str, unicode)):
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # special check for now - this will be fixed in the next major
        # gnosis release, so I don't care that the code is inline & gross
        # for now
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        if sys.version_info[0] < 3 and isinstance(thing, unicode):
            # can't pickle unicode containing the special "escape" sequence
            # we use for putting strings in the XML body (they'll be unpickled
            # as strings, not unicode, if we do!)
            if thing[0:2] == u'\xbb\xbb' and thing[-2:] == u'\xab\xab':
                raise ValueError("Unpickleable Unicode value")

            # see if it contains any XML-illegal values
            # if not is_legal_xml(thing):
            #     raise ValueError("Unpickleable Unicode value")

        if isinstance(thing, str) and getInBody(str):
            # technically, this will crash safe_content(), but I prefer to
            # have the test here for clarity
            try:
                # safe_content assumes it can always convert the string
                # to unicode, which isn't true (eg. pickle a UTF-8 value)
                _ = unicode(thing)
            except ValueError as exc:
                raise_from(ValueError("Unpickleable string value (%s): %s" % (repr(thing), exc)), None)

        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # End of temporary hack code
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        if in_body:
            start_tag = start_tag + '%s>%s' % (
                _family_type('atom', 'string', mtag, mextra), safe_content(thing))
            close_tag = close_tag.lstrip()
        else:
            start_tag = start_tag + '%s value="%s" />\n' % (
                _family_type('atom', 'string', mtag, mextra), safe_string(thing))
            close_tag = ''
    # General notes:
    #   1. When we make references, set type to referenced object
    #      type -- we don't need type when unpickling, but it may be useful
    #      to someone reading the XML file
    #   2. For containers, we have to stick the container into visited{}
    #      before pickling subitems, in case it contains self-references
    #      (we CANNOT just move the visited{} update to the top of this
    #      function, since that would screw up every _family_type() call)
    elif isinstance(thing, tuple):
        start_tag, do_copy = _tag_compound(
            start_tag, _family_type('seq', 'tuple', mtag, mextra),
            orig_thing, deepcopy)
        if do_copy:
            for item in thing:
                tag_body.append(_item_tag(item, level + 1, deepcopy))
        else:
            close_tag = ''
    elif isinstance(thing, list):
        start_tag, do_copy = _tag_compound(
            start_tag, _family_type('seq', 'list', mtag, mextra),
            orig_thing, deepcopy)
        # need to remember we've seen container before pickling subitems
        VISITED[id(orig_thing)] = orig_thing
        if do_copy:
            for item in thing:
                tag_body.append(_item_tag(item, level + 1, deepcopy))
        else:
            close_tag = ''
    elif isinstance(thing, dict):
        start_tag, do_copy = _tag_compound(
            start_tag, _family_type('map', 'dict', mtag, mextra),
            orig_thing, deepcopy)
        # need to remember we've seen container before pickling subitems
        VISITED[id(orig_thing)] = orig_thing
        if do_copy:
            for key, val in thing.items():
                tag_body.append(_entry_tag(key, val, level + 1, deepcopy))
        else:
            close_tag = ''
    else:
        raise ValueError("Non-handled type %s" % type(thing))

    # need to keep a ref to the object for two reasons -
    #  1. we can ref it later instead of copying it into the XML stream
    #  2. need to keep temporary objects around so their ids don't get reused

    # if DEEPCOPY, we can skip this -- reusing ids is not an issue if we
    # never look at them
    if not deepcopy:
        VISITED[id(orig_thing)] = orig_thing

    return start_tag + ''.join(tag_body) + close_tag


def _thing_from_dom(dom_node, container=None):
    "Converts an [xml_pickle] DOM tree to a 'native' Python object"
    for node in dom_node.childNodes:
        if not hasattr(node, '_attrs') or not node.nodeName != '#text':
            continue

        if node.nodeName == "PyObject":
            container = unpickle_instance(node)
            try:
                id_ = node.getAttribute('id')
                VISITED[id_] = container
            except KeyError:
                pass  # Accepable, not having id only affects caching

        elif node.nodeName in ['attr', 'item', 'key', 'val']:
            node_family = node.getAttribute('family')
            node_type = node.getAttribute('type')
            node_name = node.getAttribute('name')

            # check refid first (if present, type is type of referenced object)
            ref_id = node.getAttribute('refid')

            if len(ref_id):	 # might be empty or None
                if node.nodeName == 'attr':
                    setattr(container, node_name, VISITED[ref_id])
                else:
                    container.append(VISITED[ref_id])

                # done, skip rest of block
                continue

            # if we didn't find a family tag, guess (do after refid check --
            # old pickles will set type="ref" which _fix_family can't handle)
            node_family = _fix_family(node_family, node_type)

            node_valuetext = get_node_valuetext(node)

            # step 1 - set node_val to basic thing
            if node_family == 'none':
                node_val = None
            elif node_family == 'atom':
                node_val = node_valuetext
            elif node_family == 'seq':
                # seq must exist in VISITED{} before we unpickle subitems,
                # in order to handle self-references
                seq = []
                _save_obj_with_id(node, seq)
                node_val = _thing_from_dom(node, seq)
            elif node_family == 'map':
                # map must exist in VISITED{} before we unpickle subitems,
                # in order to handle self-references
                mapping = ODict()
                _save_obj_with_id(node, mapping)
                node_val = _thing_from_dom(node, mapping)
            elif node_family == 'uniq':
                # uniq is another special type that is handled here instead
                # of below.
                if node_type == 'True':
                    node_val = True
                elif node_type == 'False':
                    node_val = False
                else:
                    raise ValueError("Unknown uniq type %s" % node_type)
            else:
                raise ValueError("Unknown family %s,%s,%s" % (node_family, node_type, node_name))

            # step 2 - take basic thing and make exact thing
            # Note there are several NOPs here since node_val has been decided
            # above for certain types. However, I left them in since I think it's
            # clearer to show all cases being handled (easier to see the pattern
            # when doing later maintenance).

            # pylint: disable=self-assigning-variable
            if node_type == 'None':
                node_val = None
            elif node_type == 'numeric':
                # node_val = safe_eval(node_val)
                node_val = aton(node_val)
            elif node_type == 'string':
                node_val = node_val
            elif node_type == 'list':
                node_val = node_val
            elif node_type == 'tuple':
                # subtlety - if tuples could self-reference, this would be wrong
                # since the self ref points to a list, yet we're making it into
                # a tuple. it appears however that self-referencing tuples aren't
                # really all that legal (regular pickle can't handle them), so
                # this shouldn't be a practical problem.
                node_val = tuple(node_val)
            elif node_type == 'dict':
                node_val = node_val
            elif node_type == 'True':
                node_val = node_val
            elif node_type == 'False':
                node_val = node_val
            else:
                raise ValueError("Unknown type %s,%s" % (node, node_type))

            if node.nodeName == 'attr':
                setattr(container, node_name, node_val)
            else:
                container.append(node_val)

            _save_obj_with_id(node, node_val)

        elif node.nodeName == 'entry':
            keyval = _thing_from_dom(node, [])
            key, val = keyval[0], keyval[1]
            container[key] = val
            # <entry> has no id for refchecking

        else:
            raise ValueError("Element %s is not in PyObjects.dtd" % node.nodeName)

    return container
