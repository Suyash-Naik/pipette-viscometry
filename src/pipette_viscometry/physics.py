from dataclasses import dataclass
import math

@dataclass(frozen=True)
class ViscoResults:
    eta: float
    Pc: float
    gamma: float

def calculate_viscosity(lasp: float, lret: float, Rp: float, P: float, Rcac: float) -> ViscoResults:
    """
    Computes viscosity (eta), critical pressure (Pc), and surface tension (gamma).
    """
    denom = 2 * math.pi * (lasp + abs(lret))
    if denom == 0:
        raise ValueError("Sum of lasp and |lret| cannot be zero.")
        
    eta = (Rp * P) / denom
    Pc = P - (3 * math.pi * eta * lasp) / Rp
    gamma = (Rp * Pc) / 2.0
    
    return ViscoResults(eta=eta, Pc=Pc, gamma=gamma)