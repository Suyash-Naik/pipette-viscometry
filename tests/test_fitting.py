# tests/test_fitting.py
import numpy as np
import pytest
from pipette_viscometry.fitting import fit_span_data


def test_fit_span_data_exact():
    x = np.linspace(0, 10, 100)
    y = 2.5 * x + 1.2
    fit = fit_span_data(x, y, xmin=2.0, xmax=8.0)
    assert pytest.approx(fit.slope) == 2.5
    assert pytest.approx(fit.intercept) == 1.2

def test_fit_span_insufficient_points():
    x = np.array([1.0, 2.0])
    y = np.array([2.0, 4.0])
    with pytest.raises(ValueError, match="Insufficient points"):
        fit_span_data(x, y, xmin=0.0, xmax=3.0, min_points=3)