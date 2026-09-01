import numpy as np

from internet_half_life.study import exact_sign_flip_test, exact_sign_test


def test_exact_sign_test_is_two_sided():
    assert exact_sign_test(5, 0) == 0.0625
    assert exact_sign_test(3, 2) == 1.0
    assert exact_sign_test(0, 0) == 1.0


def test_exact_sign_flip_test_finds_a_consistent_direction():
    assert exact_sign_flip_test(np.array([-1.0, -2.0, -3.0])) == 0.25
    assert exact_sign_flip_test(np.array([])) == 1.0
