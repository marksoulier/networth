import numpy as np
from typing import Dict, List, Callable
from .base_functions import u, R

def take_net_worth_snapshot(envelopes: Dict[str, List[Callable]],
                          time_days: float,
                          frequency_days: int = 30) -> None:
    """
    Take periodic snapshots of total net worth.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        time_days: When to start taking snapshots
        frequency_days: How often to take snapshots (in days)
    """
    def snapshot(t):
        # Calculate total net worth at time t
        total = sum(sum(f(t) for f in envelope) for envelope in envelopes.values())
        return total * u(t - time_days)
    
    # Add snapshot function to a special 'NetWorth' envelope
    if 'NetWorth' not in envelopes:
        envelopes['NetWorth'] = []
    envelopes['NetWorth'].append(snapshot)

def manual_correction(envelopes: Dict[str, List[Callable]],
                     amount: float,
                     time_days: float,
                     reason: str,
                     envelope_key: str = 'Cash') -> None:
    """
    Make a manual correction to an envelope balance.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        amount: Amount to add (positive) or subtract (negative)
        time_days: When to apply the correction
        reason: Reason for the correction
        envelope_key: Which envelope to correct
    """
    def correction(t):
        return amount * u(t - time_days)
    envelopes[envelope_key].append(correction)

def apply_inflation(envelopes: Dict[str, List[Callable]],
                   inflation_rate: float,
                   time_days: float,
                   affected_envelopes: List[str]) -> None:
    """
    Apply inflation rate to specified envelopes.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        inflation_rate: Annual inflation rate
        time_days: When to start applying inflation
        affected_envelopes: List of envelope keys to apply inflation to
    """
    def inflation_adjustment(t):
        years = (t - time_days) / 365
        return (1 + inflation_rate) ** years
    
    for key in affected_envelopes:
        if key in envelopes:
            # Create a new list of functions with inflation adjustment
            adjusted_functions = []
            for f in envelopes[key]:
                adjusted_functions.append(lambda t, f=f: f(t) * inflation_adjustment(t))
            envelopes[key] = adjusted_functions 