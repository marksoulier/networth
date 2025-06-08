import numpy as np
from typing import Dict, List, Callable
from .base_functions import u, R

def add_living_expenses(envelopes: Dict[str, List[Callable]],
                       groceries: float,
                       utilities: float,
                       gas: float,
                       eating_out: float,
                       subscriptions: float,
                       time_days: float,
                       frequency_days: float = 30,
                       from_key: str = 'Cash') -> None:
    """
    Add recurring living expenses.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        groceries: Monthly grocery expense
        utilities: Monthly utilities expense
        gas: Monthly gas expense
        eating_out: Monthly eating out expense
        subscriptions: Monthly subscription expense
        time_days: When to start expenses
        frequency_days: How often expenses occur
        from_key: Which envelope to take expenses from
    """
    total_monthly = groceries + utilities + gas + eating_out + subscriptions
    
    def expenses(t):
        return -total_monthly * R(lambda x: u(x), t, time_days, time_days + 365*20, frequency_days)
    envelopes[from_key].append(expenses)

def add_rent_payment(envelopes: Dict[str, List[Callable]],
                    amount: float,
                    time_days: float,
                    frequency_days: float = 30,
                    from_key: str = 'Cash') -> None:
    """
    Add recurring rent payment.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        amount: Monthly rent amount
        time_days: When to start payments
        frequency_days: How often payments occur
        from_key: Which envelope to take payments from
    """
    def rent(t):
        return -amount * R(lambda x: u(x), t, time_days, time_days + 365*20, frequency_days)
    envelopes[from_key].append(rent)

def buy_car(envelopes: Dict[str, List[Callable]],
           car_value: float,
           loan_term_years: int,
           loan_rate: float,
           downpayment: float,
           time_days: float,
           from_key: str = 'Cash') -> None:
    """
    Purchase a car with financing.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        car_value: Total car value
        loan_term_years: Loan term in years
        loan_rate: Annual interest rate
        downpayment: Initial downpayment
        time_days: When to make the purchase
        from_key: Which envelope to take payment from
    """
    # Calculate monthly payment
    loan_amount = car_value - downpayment
    r_monthly = loan_rate / 12
    N = loan_term_years * 12
    monthly_payment = loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)
    
    # Add downpayment
    envelopes[from_key].append(lambda t: -downpayment * u(t - time_days))
    
    # Add monthly payments
    def payments(t):
        return -monthly_payment * R(lambda x: u(x), t, time_days, time_days + loan_term_years*365, 30)
    envelopes[from_key].append(payments)

def buy_boat(envelopes: Dict[str, List[Callable]],
            boat_value: float,
            loan_term_years: int,
            loan_rate: float,
            downpayment: float,
            time_days: float,
            from_key: str = 'Cash') -> None:
    """
    Purchase a boat with financing.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        boat_value: Total boat value
        loan_term_years: Loan term in years
        loan_rate: Annual interest rate
        downpayment: Initial downpayment
        time_days: When to make the purchase
        from_key: Which envelope to take payment from
    """
    # Calculate monthly payment
    loan_amount = boat_value - downpayment
    r_monthly = loan_rate / 12
    N = loan_term_years * 12
    monthly_payment = loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)
    
    # Add downpayment
    envelopes[from_key].append(lambda t: -downpayment * u(t - time_days))
    
    # Add monthly payments
    def payments(t):
        return -monthly_payment * R(lambda x: u(x), t, time_days, time_days + loan_term_years*365, 30)
    envelopes[from_key].append(payments)

def take_vacation(envelopes: Dict[str, List[Callable]],
                 total_cost: float,
                 time_days: float,
                 from_key: str = 'Cash') -> None:
    """
    Record a vacation expense.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        total_cost: Total vacation cost
        time_days: When the vacation occurs
        from_key: Which envelope to take payment from
    """
    envelopes[from_key].append(lambda t: -total_cost * u(t - time_days))

def furnish_home(envelopes: Dict[str, List[Callable]],
                total_cost: float,
                time_days: float,
                from_key: str = 'Cash') -> None:
    """
    Record home furnishing expenses.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        total_cost: Total furnishing cost
        time_days: When the purchase occurs
        from_key: Which envelope to take payment from
    """
    envelopes[from_key].append(lambda t: -total_cost * u(t - time_days)) 