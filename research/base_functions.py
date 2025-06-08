import numpy as np
from typing import Callable, Dict, List, Optional

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