from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class FitResult:
    slope: float
    intercept: float
    xmin: float
    xmax: float
    n_points: int

def fit_span_data(x: np.ndarray, y: np.ndarray, xmin: float, xmax: float, min_points: int = 3) -> FitResult:
    """
    Fits linear slope to sub-segment without display side-effects.
    """
    if xmin >= xmax:
        xmin, xmax = xmax, xmin

    indmin, indmax = np.searchsorted(x, (xmin, xmax))
    indmax = min(len(x), indmax)

    sliced_x = x[indmin:indmax]
    sliced_y = y[indmin:indmax]

    if len(sliced_x) < min_points:
        raise ValueError(f"Insufficient points in selected span: {len(sliced_x)} < {min_points}")

    slope, intercept = np.polyfit(sliced_x, sliced_y, 1)
    
    return FitResult(
        slope=float(slope),
        intercept=float(intercept),
        xmin=float(sliced_x[0]),
        xmax=float(sliced_x[-1]),
        n_points=len(sliced_x)
    )