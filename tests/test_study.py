import numpy as np

from internet_half_life.study import (
    _two_sample_permutation,
    exact_sign_flip_test,
    exact_sign_test,
)


def test_exact_sign_test_is_two_sided():
    assert exact_sign_test(5, 0) == 0.0625
    assert exact_sign_test(3, 2) == 1.0
    assert exact_sign_test(0, 0) == 1.0


def test_exact_sign_flip_test_finds_a_consistent_direction():
    assert exact_sign_flip_test(np.array([-1.0, -2.0, -3.0])) == 0.25
    assert exact_sign_flip_test(np.array([])) == 1.0


def test_two_sample_permutation_enumerates_every_partition():
    result = _two_sample_permutation(
        np.array([0.0, 1.0]),
        np.array([10.0, 11.0]),
    )
    assert np.isclose(result, 1 / 3)
