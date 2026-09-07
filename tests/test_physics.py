# tests/test_physics.py
import pytest
from pipette_viscometry.physics import calculate_viscosity

def test_calculate_viscosity_known_values():
    # Known test case
    res = calculate_viscosity(lasp=1.0, lret=-0.5, Rp=65.0, P=70.0, Rcac=367.0)
    assert pytest.approx(res.eta, rel=1e-3) ==  482.769
    assert pytest.approx(res.Pc, rel=1e-3) == 0.0

def test_calculate_viscosity_zero_division():
    with pytest.raises(ValueError, match="cannot be zero"):
        calculate_viscosity(lasp=0.0, lret=0.0, Rp=65.0, P=70.0, Rcac=367.0)