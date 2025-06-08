import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Callable, Any

# Unit step function
def u(x):
    return np.where(x >= 0, 1, 0)

# --- Time Shift Operator ---

def T(f, t, tk):
    """Shift function f by tk, enforce causality"""
    shifted_t = t - tk
    return f(shifted_t) * u(shifted_t)

# --- Recurring Operator ---

def R(f, t, t0, tf, dt):
    """Repeat function f from t0 to tf with interval dt"""
    result = np.zeros_like(t, dtype=np.float64)  # Explicitly set dtype to float64
    for k in np.arange(t0, tf + dt, dt):
        result += T(f, t, k)
    return result

def calculate_monthly_payment(loan_amount: float, annual_rate: float, years: int) -> float:
    """Calculate monthly mortgage payment"""
    r_monthly = annual_rate / 12
    N = years * 12
    return loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)

@dataclass
class HouseParameters:
    """Class to handle time-varying house parameters using piecewise functions"""
    downpayment: float
    home_value: float
    annual_rate: float
    years: int
    appreciation_rate: float
    start_time: float = 0
    
    def __post_init__(self):
        self.loan_amount = self.home_value - self.downpayment
        self.monthly_payment = calculate_monthly_payment(
            self.loan_amount, self.annual_rate, self.years
        )
        # Initialize parameter changes with starting values
        self._parameter_changes = [{
            'time': self.start_time,
            'monthly_payment': self.monthly_payment,
            'payment_day': 1,  # 1 = first of month
            'appreciation_rate': self.appreciation_rate,
            'annual_rate': self.annual_rate
        }]
    
    def evaluate_parameters(self, t: float) -> dict:
        """Evaluate all parameters at time t
        
        Args:
            t: Time in days
            
        Returns:
            Dictionary of parameter values at time t
        """
        # Find the most recent parameter set before or at time t
        current_params = self._parameter_changes[0]
        for params in sorted(self._parameter_changes, key=lambda x: x['time']):
            if params['time'] <= t:
                current_params = params
            else:
                break
        return current_params
    
    def add_parameter_change(self, time: float, **parameters):
        """Add a change to one or more parameters at a specific time
        
        Args:
            time: Time in days when the change occurs
            **parameters: Keyword arguments for parameters to change
        """
        # Get the most recent parameters before this time
        current_params = self.evaluate_parameters(time)
        # Create new parameter set with changes
        new_params = current_params.copy()
        new_params['time'] = time
        new_params.update(parameters)
        self._parameter_changes.append(new_params)
    
    def increase_monthly_payment(self, new_payment: float, time: float):
        """Schedule a monthly payment increase at a specific time"""
        self.add_parameter_change(time, monthly_payment=new_payment)
    
    def change_payment_day(self, new_day: float, time: float):
        """Schedule a change in payment day (1-31) at a specific time"""
        self.add_parameter_change(time, payment_day=new_day)
    
    def change_appreciation_rate(self, new_rate: float, time: float):
        """Schedule a change in appreciation rate at a specific time"""
        self.add_parameter_change(time, appreciation_rate=new_rate)
    
    def change_interest_rate(self, new_rate: float, time: float):
        """Schedule a change in interest rate at a specific time"""
        self.add_parameter_change(time, annual_rate=new_rate)

def buy_house(envelopes: dict, from_key: str, to_key: str, params: HouseParameters):
    """Buy a house with time-varying parameters
    
    Args:
        envelopes: Dictionary of envelope lists
        from_key: Key of the envelope to withdraw from
        to_key: Key of the envelope to deposit into
        params: HouseParameters instance containing all house parameters
    """
    # Take out downpayment
    envelopes[from_key].append(
        lambda t: T(lambda τ: -params.downpayment, t, params.start_time)
    )
    
    # Add monthly payment function that uses current parameters
    envelopes[from_key].append(
        lambda t: R(
            lambda τ: -params.evaluate_parameters(τ)['monthly_payment'],
            t,
            params.start_time,
            params.start_time + params.years * 365,
            365/12
        )
    )
    
    # Add home equity function that uses current parameters
    envelopes[to_key].append(
        lambda t: T(
            lambda τ: (params.downpayment + params.loan_amount) * 
                     (1 + params.evaluate_parameters(τ)['appreciation_rate']) ** (τ/365),
            t,
            params.start_time
        )
    )

# Example usage:
if __name__ == "__main__":
    # Create house parameters
    house_params = HouseParameters(
        downpayment=80000,
        home_value=400000,
        annual_rate=0.035,
        years=30,
        appreciation_rate=0.0427,
        start_time=3*365  # Start in 3 years
    )
    
    # Schedule some changes
    house_params.increase_monthly_payment(2200, 8*365)  # Increase payment after 8 years
    house_params.change_payment_day(15, 5*365)  # Change payment day to 15th after 5 years
    house_params.change_appreciation_rate(0.05, 10*365)  # Increase appreciation rate after 10 years
    
    # Create envelopes
    envelopes = {
        'W1': [],  # Cash
        'House': []  # House equity
    }
    
    # Add initial cash
    envelopes['W1'].append(lambda t: 500000 * u(t))
    
    # Buy the house
    buy_house(envelopes, 'W1', 'House', house_params)
    
    # Evaluate and plot
    t_range = np.arange(0, 365 * 32, 5)
    results = {}
    for key in envelopes:
        results[key] = np.zeros_like(t_range, dtype=float)
        for func in envelopes[key]:
            results[key] += np.array([func(t) for t in t_range])
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.stackplot(t_range/365, results['W1'], results['House'],
                 labels=['Cash', 'House Equity'])
    plt.title('Net Worth Composition Over Time')
    plt.xlabel('Time (Years)')
    plt.ylabel('Value ($)')
    plt.legend()
    plt.grid(True)
    plt.show()