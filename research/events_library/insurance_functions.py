import numpy as np
from typing import Dict, List, Callable
from .base_functions import u, R

def buy_health_insurance(envelopes: Dict[str, List[Callable]],
                        monthly_premium: float,
                        time_days: float,
                        deductible: float,
                        coverage_percentage: float,
                        from_key: str = 'Cash') -> None:
    """
    Add health insurance premium payments.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        monthly_premium: Monthly premium amount
        time_days: When to start payments
        deductible: Annual deductible amount
        coverage_percentage: Insurance coverage percentage
        from_key: Which envelope to take payments from
    """
    def premium(t):
        return -monthly_premium * R(lambda x: u(x), t, time_days, time_days + 365*20, 30)
    envelopes[from_key].append(premium)

def medical_expense(envelopes: Dict[str, List[Callable]],
                   total_cost: float,
                   time_days: float,
                   insurance_coverage: float,
                   deductible: float,
                   from_key: str = 'Cash') -> None:
    """
    Record a medical expense with insurance coverage.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        total_cost: Total medical cost
        time_days: When the expense occurs
        insurance_coverage: Insurance coverage percentage
        deductible: Annual deductible amount
        from_key: Which envelope to take payment from
    """
    # Calculate out-of-pocket cost
    covered_amount = total_cost * insurance_coverage
    out_of_pocket = total_cost - covered_amount
    
    # Add out-of-pocket cost
    envelopes[from_key].append(lambda t: -out_of_pocket * u(t - time_days))

def buy_life_insurance(envelopes: Dict[str, List[Callable]],
                      coverage_amount: float,
                      monthly_premium: float,
                      term_years: int,
                      time_days: float,
                      from_key: str = 'Cash') -> None:
    """
    Add life insurance premium payments.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        coverage_amount: Total coverage amount
        monthly_premium: Monthly premium amount
        term_years: Policy term in years
        time_days: When to start payments
        from_key: Which envelope to take payments from
    """
    def premium(t):
        return -monthly_premium * R(lambda x: u(x), t, time_days, time_days + term_years*365, 30)
    envelopes[from_key].append(premium)

def insurance_payout(envelopes: Dict[str, List[Callable]],
                    payout_amount: float,
                    time_days: float,
                    to_key: str = 'Cash') -> None:
    """
    Record an insurance payout.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        payout_amount: Payout amount
        time_days: When the payout occurs
        to_key: Which envelope to add payout to
    """
    envelopes[to_key].append(lambda t: payout_amount * u(t - time_days)) 