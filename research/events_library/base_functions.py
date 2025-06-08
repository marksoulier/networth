import numpy as np
from typing import Callable, Dict, List, Optional

# Unit step function
def u(x):
    return np.where(x >= 0, 1, 0)

def T(f, t, tk):
    shifted_t = t - tk
    return f(shifted_t) * u(shifted_t)

def R(f, t, t0, tf, dt):
    """Repeat function f from t0 to tf with interval dt"""
    result = np.zeros_like(t, dtype=np.float64)  # Explicitly set dtype to float64
    for k in np.arange(t0, tf + dt, dt):
        result += T(f, t, k)
    return result

def inflow(a, t):
    """
    Parameters:
        a (float): Inflow amount [USD]
    
    Instantaneous inflow of money starting at t = 0.
    """
    return a * u(t)

def outflow(b, t):
    """
    Parameters:
        b (float): Outflow amount [USD]
    
    Instantaneous outflow of money starting at t = 0.
    """
    return -b * u(t)


# Compound interest inflow and outflow
def compound_invest_inflow(a, t, r):
    return a * ((1 + r) ** (t/365))

def compound_invest_outflow(a, t, r):
    return -a * ((1 + r) ** (t/365))


#must be done after all fucntions are applied to the envelopes.
def add_correction(envelopes: Dict[str, List[Callable]], tx: float, vactual: float, envelope_key: str = 'W1'):
    """
    Add a delta correction to an envelope at a specific time.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        tx: Time of correction
        vactual: Actual value at time tx
        envelope_key: Which envelope to modify
    """
    def delta_correction(t: float, tx: float, vactual: float, wk_func: Callable[[float], float]) -> float:
        """
        Delta Correction Operator
        D[wk](t; tx, vactual) = (vactual − wk(tx)) · u(t − tx)
        
        Parameters:
            t: Current time
            tx: Time of correction
            vactual: Actual value at time tx
            wk_func: Function to evaluate at tx
        """
        return (vactual - wk_func(tx)) * u(t - tx)

    # Store current functions before adding the correction
    current_functions = envelopes[envelope_key].copy()
    
    # Create a function that sums all previous functions
    def sum_previous(t):
        return sum(func(t) for func in current_functions)
    
    # Add the correction
    envelopes[envelope_key].append(lambda t: delta_correction(t, tx, vactual, sum_previous))


def inflation_adjust(results: Dict[str, np.ndarray], t_range: np.ndarray, current_day: int, inflation_rate: float) -> Dict[str, np.ndarray]:
    """
    Adjust results for inflation to current day value.
    
    Args:
        results: Dictionary of results arrays
        t_range: Time points array
        current_day: The reference day to adjust to (in days)
        inflation_rate: Annual inflation rate (e.g., 0.03 for 3%)
    
    Returns:
        Dictionary of inflation-adjusted results
    """
    # Convert annual inflation rate to daily rate
    daily_rate = (1 + inflation_rate) ** (1/365) - 1
    
    # Calculate inflation adjustment factors
    adjustment_factors = np.exp(-daily_rate * (current_day - t_range))
    
    # Apply adjustment to all results
    adjusted_results = {}
    for key in results:
        adjusted_results[key] = results[key] * adjustment_factors
    
    return adjusted_results

def evaluate_results(envelopes: Dict[str, List[Callable]], start_day: int, end_day: int, frequency: int, 
                    current_day: Optional[int] = None, inflation_rate: Optional[float] = None) -> Dict[str, np.ndarray]:
    """
    Evaluate the results of envelope functions over a time range and optionally apply inflation adjustment.
    
    Args:
        envelopes: Dictionary containing envelope functions
        start_day: Start day for evaluation
        end_day: End day for evaluation
        frequency: Frequency of evaluation points in days
        current_day: Optional day to adjust values to (for inflation adjustment)
        inflation_rate: Optional annual inflation rate for adjustment
        
    Returns:
        Dictionary containing arrays of evaluated results for each envelope
    """
    t_range = np.arange(start_day, end_day, frequency)
    results = {key: np.zeros_like(t_range, dtype=float) for key in envelopes}
    
    for key in envelopes:
        for func in envelopes[key]:
            results[key] += np.array([func(t) for t in t_range])
    
    # Apply inflation adjustment if parameters are provided
    if current_day is not None and inflation_rate is not None:
        results = inflation_adjust(results, t_range, current_day, inflation_rate)
            
    return results


import numpy as np
import matplotlib.pyplot as plt
from typing import Dict


def show_visual(results: Dict[str, np.ndarray], t_range: np.ndarray):
    # Calculate total net worth
    total_net_worth = np.zeros_like(t_range, dtype=np.float64)
    for key in results:
        total_net_worth += results[key]

    labels = []
    for key in results:
        labels.append(key)

    plt.figure(figsize=(12, 6))
    plt.stackplot(t_range / 365, *results.values(), labels=labels)
    plt.plot(t_range / 365, total_net_worth, 'k--', label='Total Net Worth')
    plt.title('Net Worth Composition Over Time')
    plt.xlabel('Time (Years)')
    plt.ylabel('Value ($)')
    plt.legend()
    plt.grid(True)
    plt.show()