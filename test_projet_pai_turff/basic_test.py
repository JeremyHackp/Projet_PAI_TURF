import numpy as np

from projet_pai_turff.my_module import other_function, typed_function

# -------------------------
# Tests non graphiques
# -------------------------


def test_typed_function():
    assert not typed_function(np.zeros(10), "")
    assert not typed_function(np.zeros(10), "hello")
    assert not typed_function(np.ones(5))


def test_other_function():
    other_function()
