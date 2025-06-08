from typing import Dict, List, Callable
from .base_functions import R, inflow

def get_a_job(envelopes: Dict[str, List[Callable]], to_key: str, salary: float, pay_period: float, start_time: float, end_time: float = None):
    """
    Add job income to the cash envelope.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        salary: Annual salary
        pay_period: Pay period in days
        start_time: When the job starts
        end_time: When the job ends (optional)
    """
    # Calculate pay per period
    pay_per_period = salary * pay_period / 365
    
    # If no end time specified, use 50 years from start (reasonable retirement age)
    if end_time is None:
        end_time = start_time + 50 * 365
    
    # Add recurring income
    envelopes[to_key].append(lambda t: R(lambda τ: inflow(pay_per_period, τ), t, start_time, end_time, pay_period))
