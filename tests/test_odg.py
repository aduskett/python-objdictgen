import os
import pytest
from objdictgen.__main__ import main


@pytest.mark.parametrize("suffix", ['.od', '.json', '.eds'])
def test_odg_list(odfile, suffix):

    fname = odfile + suffix
    if not os.path.exists(fname):
        pytest.skip("File not found")

    main((
        'list',
        fname
    ))
