from app.signal.welford import WelfordStats


def test_welford_matches_closed_form_mean_and_variance():
    xs = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    w = WelfordStats()
    for x in xs:
        w.update(x)
    # closed-form: mean = 5, variance (population) = 4.0
    assert abs(w.mean - 5.0) < 1e-9
    # Welford here is population variance (m2/n)
    assert abs(w.variance - 4.0) < 1e-9


def test_zscore_is_zero_for_too_few_samples():
    w = WelfordStats()
    for x in [1.0, 2.0, 3.0]:
        w.update(x)
    # n < 10 → zscore returns 0 guard
    assert w.zscore(100.0) == 0.0
