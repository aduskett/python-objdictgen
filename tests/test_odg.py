import pytest
from objdictgen.__main__ import main


@pytest.mark.parametrize("suffix", ['.od', '.json', '.eds'])
def test_odg_list(odfile, suffix):

    main((
        'list',
        odfile + suffix
    ))
