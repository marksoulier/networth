import numpy as np
from typing import Dict, List, Callable
from .base_functions import u, R

def get_a_job(envelopes: Dict[str, List[Callable]], 
              to_key: str,
              salary: float,
              pay_period: int,
              start_time: float,
              end_time: float,
              federal_tax: float = 0.15,
              state_tax: float = 0.05,
              social_security: float = 0.062,
              medicare: float = 0.0145,
              retirement_contribution: float = 0.05,
              retirement_match: float = 0.05) -> None:
    """
    Add a job income stream to an envelope.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        to_key: Which envelope to add income to
        salary: Annual salary
        pay_period: Number of pay periods per year
        start_time: When to start the income
        end_time: When to end the income
        federal_tax: Federal income tax rate
        state_tax: State income tax rate
        social_security: Social security tax rate
        medicare: Medicare tax rate
        retirement_contribution: 401k contribution rate
        retirement_match: Employer 401k match rate
    """
    # Calculate net pay per period
    gross_per_period = salary / pay_period
    total_tax_rate = federal_tax + state_tax + social_security + medicare
    net_per_period = gross_per_period * (1 - total_tax_rate)
    
    # Calculate retirement contributions
    employee_contribution = gross_per_period * retirement_contribution
    employer_match = gross_per_period * retirement_match
    
    # Add net pay to cash envelope
    def net_pay(t):
        return net_per_period * R(lambda x: u(x), t, start_time, end_time, 365/pay_period)
    envelopes[to_key].append(net_pay)
    
    # Add retirement contributions to retirement envelope
    if 'Retirement' in envelopes:
        def retirement_contrib(t):
            return (employee_contribution + employer_match) * R(lambda x: u(x), t, start_time, end_time, 365/pay_period)
        envelopes['Retirement'].append(retirement_contrib)

def start_business(envelopes: Dict[str, List[Callable]],
                  initial_investment: float,
                  time_days: float,
                  from_key: str = 'Cash') -> None:
    """
    Start a business with initial investment.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        initial_investment: Initial investment amount
        time_days: When to make the investment
        from_key: Which envelope to take investment from
    """
    # Add initial investment as outflow
    envelopes[from_key].append(lambda t: -initial_investment * u(t - time_days))

def business_income(envelopes: Dict[str, List[Callable]],
                   monthly_income: float,
                   time_days: float,
                   to_key: str = 'Cash') -> None:
    """
    Add business income stream.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        monthly_income: Monthly income amount
        time_days: When to start the income
        to_key: Which envelope to add income to
    """
    def income(t):
        return monthly_income * R(lambda x: u(x), t, time_days, time_days + 365*20, 30)
    envelopes[to_key].append(income)

def business_loss(envelopes: Dict[str, List[Callable]],
                 loss_amount: float,
                 time_days: float,
                 from_key: str = 'Cash') -> None:
    """
    Record a business loss.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        loss_amount: Amount of the loss
        time_days: When the loss occurs
        from_key: Which envelope to take loss from
    """
    envelopes[from_key].append(lambda t: -loss_amount * u(t - time_days))

def start_retirement(envelopes: Dict[str, List[Callable]],
                    monthly_withdrawal: float,
                    time_days: float,
                    from_key: str = 'Retirement',
                    to_key: str = 'Cash') -> None:
    """
    Start retirement withdrawals.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        monthly_withdrawal: Monthly withdrawal amount
        time_days: When to start withdrawals
        from_key: Which envelope to take withdrawals from
        to_key: Which envelope to add withdrawals to
    """
    def withdrawal(t):
        return monthly_withdrawal * R(lambda x: u(x), t, time_days, time_days + 365*30, 30)
    envelopes[from_key].append(lambda t: -withdrawal(t))
    envelopes[to_key].append(withdrawal) 