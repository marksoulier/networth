import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable, Any

# Time resolution in days
t_range = np.arange(0, 365 * 32, 5)  # 10 years, daily steps


# --- Resourceful Functions ---
def calculate_monthly_payment(loan_amount, annual_rate, years):
    r_monthly = annual_rate / 12
    N = years * 12
    return loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)

#Closed form forumla for calculating the principle paid at month_index n from the start of the loan.
def principal_paid(loan_amount, annual_rate, years, month_index):
    i = annual_rate / 12
    N = years * 12
    k = month_index

    numerator = (1 + i)**k - 1
    denominator = (1 + i)**N - 1

    return loan_amount * (numerator / denominator)



# Unit step function
def u(x):
    return np.where(x >= 0, 1, 0)

# --- Base Functions ---

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

def simple_interest(principal, rate, t):
    """
    Parameters:
        principal (float): Initial invested or borrowed amount [USD]
        rate (float): Simple interest rate per unit time [1/time]
    
    Linear interest accumulation over time.
    """
    return principal * rate * t * u(t)

def compound_interest(principal, rate, t):
    """
    Parameters:
        principal (float): Initial invested or borrowed amount [USD]
        rate (float): Compound interest rate per unit time [1/time], per day
    
    Exponential interest accumulation over time.
    Used for asset vlaue over time, depreciation or inflation
    """
    return principal * (1 + rate) ** (t / 365) * u(t)

def depreciation_schedule(cost, life_span, t):
    """
    Parameters:
        cost (float): Initial asset cost [USD]
        life_span (float): Asset's useful lifetime [time]
    
    Straight-line depreciation model across a defined lifespan.
    Used by GAAP and IRS for asset value overtime
    """
    return -(cost / life_span) * (t <= life_span) * u(t)

    
    
def home_equity(downpayment, appreciation, loan_amount, annual_rate, years, t):
    """Calculate the total equity in a home given appreciation for the home over time and a morgage payment schedule
    
    Parameters:
        downpayment (float): Downpayment amount [USD]
        appreciation (float): Appreciation rate per year [1/year]
        loan_amount (float): Loan amount [USD]
        annual_rate (float): Annual interest rate [1/year]
        years (float): Number of years of the loan
        t (float): Time [days]
    """
    month_index = int(t // (365 / 12))
    principle_paid = principal_paid(loan_amount=loan_amount, annual_rate=annual_rate, years=years, month_index=month_index)
    total_value = (downpayment + principle_paid) * (1 + appreciation) ** (t / 365)
    return total_value


def home_equity_with_home_value(downpayment, appreciation, loan_amount, original_home_value, current_home_value, annual_rate, years, t):
    """Caclualte the home value with a given known home value at a certain point in time

    Args:
        appreciation (float): Appreciation rate per year [1/year]
        loan_amount (float): Loan amount [USD]
        home_value (float): Home value [USD]
        rate (float): Interest rate per year [1/year]
        years (float): Number of years of the loan
        t (float): Time [days]
    """
    month_index = int(t // (365 / 12))
    principle_paid = principal_paid(loan_amount=loan_amount, annual_rate=annual_rate, years=years, month_index=month_index)
    total_value = (downpayment + principle_paid)/original_home_value * current_home_value * (1 + appreciation) ** (t / 365)
    return total_value



def car_equity(downpayment, depreciation, loan_amount, rate, years, initial_drop, t):
    """Calculate the total equity in a car given depreciation for the car over time and a loan payment schedule
    
    Parameters:
        downpayment (float): Downpayment amount [USD]
        depreciation (float): Depreciation rate per year [1/year] (negative value)
        loan_amount (float): Loan amount [USD]
        rate (float): Interest rate per year [1/year]
        years (float): Number of years of the loan
        t (float): Time [days]
    """
    month_index = int(t // (365 / 12))
    principle_paid = principal_paid(loan_amount=loan_amount, annual_rate=rate, years=years, month_index=month_index)
    
    # Calculate total initial value
    initial_value = downpayment + loan_amount
    
    # Apply immediate depreciation when t > 0
    if t > 0:
        initial_value *= (1 - initial_drop)
    
    # Then apply ongoing depreciation from that point
    total_value = (initial_value * (1 + depreciation) ** (t / 365)) - loan_amount + principle_paid
    return total_value

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



# --- Envelope Events ---

def apply_transfer(envelopes, from_env, to_env, amount, time):
    """
    Applies a one-time transfer from one envelope to another.

    Parameters:
        envelopes (dict): Dictionary of envelope lists
        from_key (str): Key of the envelope to withdraw from
        to_key (str): Key of the envelope to deposit into
        amount (float): Transfer amount [USD]
        time (float): Time of the transfer [days]
    """
    envelopes[from_env].append(lambda t: T(lambda τ: outflow(amount, τ), t, time))
    envelopes[to_env].append(lambda t: T(lambda τ: inflow(amount, τ), t, time))


@dataclass
class TimeVaryingParameter:
    """A class to handle parameters that change over time using envelope-style function appending.
    
    Parameters:
        initial_value (Any): Initial value of the parameter
        name (str): Name of the parameter for identification
    """
    initial_value: Any
    name: str
    _changes: List[Tuple[float, Any]] = None
    
    def __post_init__(self):
        self._changes = [(0, self.initial_value)]
    
    def add_change(self, time: float, value: Any):
        """Add a new parameter change at a specific time.
        
        Args:
            time (float): Time in days when the change occurs
            value (Any): New value for the parameter
        """
        self._changes.append((time, value))
    
    def get_envelope_functions(self, time: float = 0) -> List[Callable]:
        """Get a list of functions to append to an envelope for this parameter.
        
        Args:
            time (float): Base time for the parameter changes
            
        Returns:
            List[Callable]: List of functions to append to an envelope
        """
        functions = []
        for change_time, value in sorted(self._changes):
            # Create a function that returns the value after the change time
            functions.append(lambda t, ct=change_time + time, v=value: v * u(t - ct))
        return functions

def buy_house(envelopes, from_key, to_key, downpayment, appreciation, home_value, rate, years, time, payment_schedule: TimeVaryingParameter = None):
    """Event for buying a house at a given time with given expectations."""
    loan_amount = home_value - downpayment
    monthly_payment = calculate_monthly_payment(loan_amount=loan_amount, annual_rate=rate, years=years)
    interval = 365 / 12  # once a month
    final_time = years * 365 + time
    
    # Initialize payment schedule if not provided
    if payment_schedule is None:
        payment_schedule = TimeVaryingParameter(monthly_payment, "monthly_payment")
    
    # Take out downpayment from cash envelope
    envelopes[from_key].append(lambda t: T(lambda τ: outflow(downpayment, τ), t, time))
    
    # Add payment functions to the envelope
    for payment_func in payment_schedule.get_envelope_functions(time):
        envelopes[from_key].append(lambda t: R(
            lambda τ: outflow(payment_func(τ), τ),
            t, time, final_time, interval
        ))
    
    # Place a function to calculate home equity on the house equity envelope
    envelopes[to_key].append(lambda t: T(
        lambda τ: home_equity(downpayment, appreciation, loan_amount, rate, years, τ),
        t, time
    ))

def buy_car(envelopes, from_key, to_key, downpayment, depreciation, car_value, rate, years, time, payment_schedule: TimeVaryingParameter = None, depreciation_schedule: TimeVaryingParameter = None):
    """Event for buying a car at a given time with given expectations.
    
    Parameters:
        envelopes (dict): Dictionary of envelope lists
        from_key (str): Key of the envelope to withdraw from
        to_key (str): Key of the envelope to deposit into
        downpayment (float): Downpayment amount [USD]
        depreciation (float): Initial depreciation rate per year [1/year] (negative value)
        car_value (float): Car value [USD]
        rate (float): Interest rate per year [1/year]
        years (float): Number of years of the loan
        time (float): Time of the transfer [days]
        payment_schedule (TimeVaryingParameter): Schedule of payment changes over time
        depreciation_schedule (TimeVaryingParameter): Schedule of depreciation rate changes over time
    """
    loan_amount = car_value - downpayment
    monthly_payment = calculate_monthly_payment(loan_amount=loan_amount, annual_rate=rate, years=years)
    interval = 365 / 12  # once a month
    final_time = years * 365 + time
    initial_drop = 0.10  # 10% immediate depreciation when driving off the lot
    
    # Initialize payment schedule if not provided
    if payment_schedule is None:
        payment_schedule = TimeVaryingParameter(monthly_payment, "monthly_payment")
    
    # Initialize depreciation schedule if not provided
    if depreciation_schedule is None:
        depreciation_schedule = TimeVaryingParameter(depreciation, "depreciation_rate")
    
    # Take out downpayment from cash envelope
    envelopes[from_key].append(lambda t: T(lambda τ: outflow(downpayment, τ), t, time))
    
    # Add payment functions to the envelope
    for payment_func in payment_schedule.get_envelope_functions(time):
        envelopes[from_key].append(lambda t: R(
            lambda τ: outflow(payment_func(τ), τ),
            t, time, final_time, interval
        ))
    
    # Place a function to calculate car equity on the car equity envelope with variable depreciation
    for depreciation_func in depreciation_schedule.get_envelope_functions(time):
        envelopes[to_key].append(lambda t: T(
            lambda τ: car_equity(
                downpayment,
                depreciation_func(τ),
                loan_amount,
                rate,
                years,
                initial_drop,
                τ
            ),
            t, time
        ))


def get_a_job(envelopes, from_key, salary, pay_period, time, time_end):
    """Event for getting a job at a given time with given expectations.
    
    Parameters:
        envelopes (dict): Dictionary of envelope lists
        from_key (str): Key of the envelope to withdraw from
        salary (float): Salary amount [USD]
        pay_period (float): Pay period [days]
        time (float): Time of the transfer [days]
    """
    # calculate the pay per pay period
    pay_per_period = salary * pay_period / 365
    
    envelopes[from_key].append(lambda t: R(lambda τ: inflow(pay_per_period, τ), t, time, time_end, pay_period))


def rent_a_house(envelopes, from_key, rent, time, time_end):
    """ Rent a house or apartment giving monthly rent"""
    envelopes[from_key].append(lambda t: R(lambda τ: outflow(rent, τ), t, time, time_end, 365 / 12))

def savings_account_with_interest(envelopes, from_key, to_key, amount, interest, time, time_end):
    """ Save Money in a savings account with """
    envelopes[from_key].append(lambda t: R(lambda τ: outflow(interest, τ), t, time, time_end, 365 / 12))
    envelopes[to_key].append(lambda t: R(lambda τ: compound_interest(amount, interest, τ), t, time, time_end, 365 / 12))





# --- Functions for restablishing truth in envelope values --- 

def reset_home_value(envelopes, from_key, to_key, downpayment, appreciation, loan_amount, original_home_value, current_home_value, rate, years, time):
    """Reset the home value to a known home value at a given time
    
    Parameters:
        envelopes (dict): Dictionary of envelope lists
        from_key (str): Key of the envelope to withdraw from
        to_key (str): Key of the envelope to deposit into
        home_value (float): Home value [USD]
        time (float): Time of the transfer [days]
    """
    # Remove old home value function by applying a negative of it with a time shift of this time
    envelopes[from_key].append(lambda t: -T(lambda τ: home_equity(downpayment, appreciation, loan_amount, rate, years, τ), t, time))
    # Add new home value function by applying a positive of it with a time shift of this time
    envelopes[to_key].append(lambda t: T(lambda τ: home_equity_with_home_value(downpayment, appreciation, loan_amount, original_home_value, current_home_value, rate, years, τ), t, time))
    
    
    


# --- Envelope Structure ---

envelopes = {
    'W1': [],
    'W2': [],
    'House': [],
    'Car': []
}

buy_house_date = 3 * 365

#Inflow of money to pay of rhouse 
envelopes['W1'].append(lambda t: inflow(500000, t)) #start with 50k in cash

# Buying a home for 400000 with 20% downpayment, 3.5% interest rate, 30 year mortgage
mortgage_payment_schedule = TimeVaryingParameter(1800, "monthly_payment")
mortgage_payment_schedule.add_change(5*365, 2200)  # Change after 3 years
#mortgage_payment_schedule.add_change(8*365, 2500)  # Change after 8 years
buy_house(envelopes=envelopes, from_key='W1', to_key='House', downpayment=80000, appreciation=0.0427, home_value=400000, rate=0.035, years=30, time=buy_house_date, payment_schedule=mortgage_payment_schedule)

#rent a house for 1500 a month instead of buying
# rent_a_house(envelopes=envelopes, from_key='W1', rent=1500, time=buy_house_date, time_end=20*365)

# Example usage:
buy_car_date = 1*365  # 100 days after start
# Buying a car for 30000 with 20% downpayment, 5% interest rate, 5 year loan, -15% annual depreciation
car_payment_schedule = TimeVaryingParameter(500, "monthly_payment")
car_payment_schedule.add_change(1*365, 600)  # Increase after 1 year

#car_depreciation_schedule = TimeVaryingParameter(-0.15, "depreciation_rate")

#buy_car(envelopes=envelopes, from_key='W1', to_key='Car', downpayment=6000, depreciation=-0.15, 
#        car_value=30000, rate=0.05, years=5, time=buy_car_date,
#        payment_schedule=car_payment_schedule,
#        depreciation_schedule=car_depreciation_schedule)

# Pay about 3000 a month for home goods
#envelopes['W1'].append(lambda t: R(lambda τ: outflow(3000, τ), t, 0, t_range[-1], 365 / 12))

#Get a job a day 3
#get_a_job(envelopes=envelopes, from_key='W1', salary=100000, pay_period=365 / 24, time=3, time_end=20*365)

# Save 1000 a month in a savings account with 3% interest
#savings_account_with_interest(envelopes=envelopes, from_key='W1', to_key='W2', amount=2000, interest=0.03, time=3, time_end=20*365)





# # Problem Setup: Salary & Rent into W1
# salary_amount = 3000
# rent_amount = 1000
# interval_days = 30

# # Recurring salary every 30 days starting day 0
# envelopes['W1'].append(lambda t: R(lambda τ: inflow(salary_amount, τ), t, 0, t_range[-1], interval_days))

# # Recurring rent every 30 days starting day 5
# envelopes['W1'].append(lambda t: R(lambda τ: outflow(rent_amount, τ), t, 5, t_range[-1], interval_days))








# --- Evaluation and Plotting ---
if __name__ == "__main__":
    # Evaluate envelopes over time
    results = {}
    for key in envelopes:
        results[key] = np.zeros_like(t_range, dtype=float)
        for func in envelopes[key]:
            results[key] += np.array([func(t) for t in t_range])

    # Sum of all envelopes
    W_total = sum(results.values())

    print(results['House'][0:10])
    print(results['W1'][0:10])

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.stackplot(t_range / 365,  # convert to years for readability
                  results['W1'], results['W2'], results['House'], results['Car'],
                  labels=['Cash (W1)', 'Investment (W2)', 'House Equity', 'Car Equity'])
    plt.plot(t_range / 365, W_total, color='black', linestyle='--', label='Total Net Worth')
    plt.title('Net Worth Composition Over Time (Salary and Rent)')
    plt.xlabel('Time (Years)')
    plt.ylabel('Value ($)')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
