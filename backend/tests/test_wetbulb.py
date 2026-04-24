from app.signal.wetbulb import heat_stress_level, wet_bulb_c


def test_wetbulb_reference_values():
    # Stull 2011 table: T=20, RH=50 → WBT ≈ 13.7
    assert abs(wet_bulb_c(20, 50) - 13.7) < 0.5
    # T=30, RH=70 → WBT ≈ 25.4
    assert abs(wet_bulb_c(30, 70) - 25.4) < 0.5
    # T=35, RH=80 → WBT ≈ 31.5
    assert abs(wet_bulb_c(35, 80) - 31.5) < 0.7


def test_heat_stress_bands():
    assert heat_stress_level(20) == "safe"
    assert heat_stress_level(26) == "elevated"
    assert heat_stress_level(29) == "high"
    assert heat_stress_level(33) == "extreme"
