import numpy as np
from dataclasses import dataclass
from typing import List, Callable, Dict, Tuple, Optional
from .base_functions import u

def calculate_monthly_payment(loan_amount: float, annual_rate: float, years: int) -> float:
    r_monthly = annual_rate / 12
    N = years * 12
    return loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)

@dataclass
class AmortizationEntry:
    month: int
    payment: float
    principal: float
    interest: float
    remaining_balance: float

def generate_amortization_schedule(loan_amount: float, annual_rate: float, years: int) -> List[AmortizationEntry]:
    """Generate complete amortization schedule"""
    r_monthly = annual_rate / 12
    N = int(years * 12)  # Convert to integer
    monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, years)
    
    schedule = []
    balance = loan_amount
    
    for month in range(N):
        interest = balance * r_monthly
        principal = monthly_payment - interest
        balance -= principal
        
        schedule.append(AmortizationEntry(
            month=month,
            payment=monthly_payment,
            principal=principal,
            interest=interest,
            remaining_balance=balance
        ))
    
    return schedule

def adjust_home_value(params_func: Callable[[float], Dict[str, float]], t_set: float, new_value: float) -> Callable[[float], Dict[str, float]]:
    """
    Creates a new parameter function that includes a home value adjustment at a specific time.
    
    Parameters:
        params_func: Original parameter function
        t_set: Time when the new home value should be set
        new_value: New home value to set
    """
    def new_params_func(t):
        params = params_func(t)
        if t >= t_set:
            params['home_value'] = new_value
            params['t_set'] = t_set
        return params
    return new_params_func


@dataclass
class PaymentSchedule:
    payments: List[Tuple[int, float, float]]  # (id, time, amount)
    
    def change_payment(self, payment_id: int, new_amount: float, new_date: float):
        """Change a specific payment's amount and date"""
        for i, (pid, time, amount) in enumerate(self.payments):
            if pid == payment_id:
                self.payments[i] = (pid, new_date, new_amount)
                return
        raise ValueError(f"Payment ID {payment_id} not found")

def create_payment_schedule(amortization_schedule: List[AmortizationEntry], 
                          start_time: float,
                          payment_changes: List[Tuple[int, float, float]] = None) -> List[Tuple[int, float, float]]:
    """Create a payment schedule with any changes applied"""
    payments = []
    for i, entry in enumerate(amortization_schedule):
        payment_time = start_time + i * (365/12)
        amount = entry.payment
        
        # Check if this payment has been changed
        if payment_changes:
            for pid, new_time, new_amount in payment_changes:
                if pid == i:
                    payment_time = new_time
                    amount = new_amount
                    break
        
        payments.append((i, payment_time, amount))
    return payments

def create_home_value_function(initial_value: float, initial_time: float, value_changes: List[Tuple[float, float]]) -> Callable[[float], Dict[str, float]]:
    """
    Create a complete home value function with all value changes.
    
    Parameters:
        initial_value: Initial home value
        initial_time: When the home is purchased
        value_changes: List of (time, value) tuples for value changes
    """
    def home_params(t):
        return {
            'home_value': initial_value,
            't_set': initial_time
        }
    
    # Apply all value changes in sequence
    for change_time, new_value in value_changes:
        home_params = adjust_home_value(home_params, change_time, new_value)
    
    return home_params

def buy_house(envelopes: Dict[str, List[Callable]], 
             start_time: float,
             downpayment: float,
             annual_rate: float,
             years: int,
             appreciation_rate: float,
             payment_changes: List[Tuple[int, float, float]] = None,  # (id, time, amount)
             params_func: Callable[[float], Dict[str, float]] = None):
    """
    Function to handle house buying logic with time-varying parameters.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        start_time: When to buy the house
        downpayment: Initial downpayment
        annual_rate: Mortgage interest rate
        years: Loan term in years
        appreciation_rate: Annual home appreciation rate
        payment_changes: List of payment changes (id, time, amount)
        params_func: Function that returns home value parameters for a given time t
    """
    # Calculate loan amount and create amortization schedule
    initial_params = params_func(0) if params_func else {'home_value': 0, 't_set': start_time}
    home_value = initial_params['home_value']
    loan_amount = home_value - downpayment
    base_payment = calculate_monthly_payment(loan_amount, annual_rate, years)
    amortization_schedule = generate_amortization_schedule(loan_amount, annual_rate, years)
    
    # Create payment schedule once
    payment_schedule = create_payment_schedule(amortization_schedule, start_time, payment_changes)
    
    def calculate_equity(t: float) -> float:
        """Calculate home equity at time t"""
        if t < start_time:
            return 0
            
        # Get current parameters
        current_params = params_func(t) if params_func else initial_params
        current_home_value = current_params['home_value']
        t_set = current_params['t_set']
        
        # Calculate total principal paid up to time t
        principal_paid = 0
        for payment_id, payment_time, amount in payment_schedule:
            if payment_time <= t:
                # Find the corresponding amortization entry
                month_index = int((payment_time - start_time) / (365/12))
                if month_index < len(amortization_schedule):
                    base_principal = amortization_schedule[month_index].principal
                    # Add the difference between actual payment and base payment to principal
                    principal_paid += (amount - base_payment) + base_principal
        
        # Remaining loan balance
        remaining_loan = loan_amount - principal_paid
        
        # Home value at time t with appreciation
        home_value = current_home_value * (1 + appreciation_rate) ** ((t - t_set) / 365)
        
        # Equity = home value - remaining loan
        if home_value == 0: # for when the house sells no more loan is owed
            return 0
        
        return home_value - remaining_loan
    
    # Add downpayment to cash envelope (negative since it's an outflow)
    envelopes['W1'].append(lambda t: -downpayment * u(t - start_time))
    
    # Add payments from the schedule
    for payment_id, payment_time, amount in payment_schedule:
        envelopes['W1'].append(lambda t, pt=payment_time, amt=amount: -amt * u(t - pt))
    
    # Add home equity calculation
    envelopes['House'].append(calculate_equity)

def sell_house(envelopes: Dict[str, List[Callable]], sale_time: float, sale_price: float, params_func: Callable[[float], Dict[str, float]]):
    """
    Sell the house by updating home value and handling equity.
    
    Parameters:
        envelopes: Dictionary of envelope lists
        sale_time: When to sell the house
        sale_price: Sale price of the house
        params_func: Function that returns home value parameters
    """
    # First update home value to sale price (one day before sale)
    params_func = adjust_home_value(params_func, sale_time - 1, sale_price)
    
    # Then set home value to 0 at sale time
    params_func = adjust_home_value(params_func, sale_time, 0)
    
    return params_func

def sell_house_and_transfer(envelopes: Dict[str, List[Callable]], from_key: str, to_key: str, time_days: int, selling_price: Optional[float] = None) -> None:
    """
    Sell a house and transfer the equity to another envelope.
    
    Args:
        envelopes: Dictionary containing envelope functions
        from_key: Key of the envelope containing the house equity
        to_key: Key of the envelope to receive the sale proceeds
        time_days: Time in days when the sale occurs
        selling_price: Optional selling price. If not provided, uses the current equity value
    """
    # Calculate the equity value at sale time
    equity_value = sum(func(time_days-1) for func in envelopes[from_key])
    
    # If selling_price is provided, use it instead of the equity value
    if selling_price is not None:
        equity_value = selling_price
    
    # Add the equity value as cash inflow at sale time
    envelopes[to_key].append(lambda t: equity_value * u(t - time_days))

def new_appraisal(home_value_changes: List[Tuple[int, float]], time_days: int, appraised_value: float) -> None:
    """
    Add a new appraisal to the home value changes list.
    
    Args:
        home_value_changes: List of tuples containing (time_days, value) pairs
        time_days: Time in days when the appraisal occurs
        appraised_value: New appraised value of the home
    """
    home_value_changes.append((time_days, appraised_value))

def sell_home(home_value_changes: List[Tuple[int, float]], time_days: int) -> None:
    """
    Add a sale event to the home value changes list, setting value to 0.
    
    Args:
        home_value_changes: List of tuples containing (time_days, value) pairs
        time_days: Time in days when the sale occurs
    """
    home_value_changes.append((time_days, 0))

def change_payment(payment_changes: List[Tuple[int, int, float]], index: int, time_days: int, amount: float) -> None:
    """
    Add a payment change to the payment changes list.
    
    Args:
        payment_changes: List of tuples containing (index, time_days, amount)
        index: The payment index/number
        time_days: Time in days when the payment change occurs
        amount: The new payment amount
    """
    payment_changes.append((index, time_days, amount))
