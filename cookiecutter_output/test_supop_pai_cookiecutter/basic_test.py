import numpy as np

from supop_pai_cookiecutter.my_module import typed_function


def test_typed_function():
    assert not typed_function(np.zeros(10), "")
