
import objdictgen.objdictgen


# def test_odsetup(odfile, fn):
#     """ Test that we have the same od files present in DUT as in REF """
#     reffile = odfile.replace(fn.DUT, fn.REF)
#     d = list(fn.diff(reffile + '.od', odfile + '.od'))
#     assert not d


def test_objdictgen(mocker, odfile, fn):
    """ Test that objdictgen generates equal output as reference """
    mocker.patch("sys.argv", [
        "objdictgen",
        odfile + '.od',
        odfile + '.c',
    ])

    objdictgen.objdictgen.main()

    assert not list(fn.diff_ref(odfile + '.c'))
    assert not list(fn.diff_ref(odfile + '.h'))
    assert not list(fn.diff_ref(odfile + '_objectdefines.h'))
