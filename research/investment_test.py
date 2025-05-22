import numpy as np
import matplotlib.pyplot as plt



# Modular loan structure
def calculate_monthly_payment(loan_amount, annual_rate, years):
    r_monthly = annual_rate / 12
    N = years * 12
    return loan_amount * (r_monthly * (1 + r_monthly) ** N) / ((1 + r_monthly) ** N - 1)


# Define the parameters
r = 0.05  # investment interest rate
t_range = np.arange(0, 105, 1/12)  # time from 0 to 105 years

# Define unit step function
def u(x):
    return np.where(x >= 0, 1, 0)

# Basic inflow and outflow
def inflow(a, tk, t):
    return a * u(t - tk)

def outflow(a, tk, t):
    return -a * u(t - tk)

# Compound interest inflow and outflow
def compound_invest_inflow(a, tk, t):
    return a * ((1 + r) ** (t - tk)) * u(t - tk)

def compound_invest_outflow(a, tk, t):
    return -a * ((1 + r) ** (t - tk)) * u(t - tk)

# Recurring inflow and outflow
def recurring_inflow(a, t_start, t_end, t, interval=1):
    return sum(inflow(a, k, t) for k in np.arange(t_start, t_end + interval, interval))

def recurring_outflow(a, t_start, t_end, t, interval=1):
    return sum(outflow(a, k, t) for k in np.arange(t_start, t_end + interval, interval))

def recurring_inflow_compound_interest(a, t_start, t_end, t):
    return sum(compound_invest_inflow(a, k, t) for k in range(t_start, t_end + 1))

def recurring_outflow_compound_interest(a, t_start, t_end, t):
    return sum(compound_invest_outflow(a, k, t) for k in range(t_start, t_end + 1))

def recurring_loan_outflow(V, D, annual_rate, term_years, start_age):
    loan_amount = V - D
    monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, term_years)
    def outflow_func(t):
        return recurring_outflow(monthly_payment, start_age, start_age + term_years, t, interval=1/12)
    return outflow_func

def recurring_loan_inflow(V, D, annual_rate, term_years, start_age):
    loan_amount = V - D
    monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, term_years)
    def inflow_func(t):
        return recurring_inflow(monthly_payment, start_age, start_age + term_years, t, interval=1/12)
    return inflow_func

# Depreciating or appreciating asset value
def asset_value(C, rate, start_age):
    def value_func(t):
        return C * ((1 + rate) ** (t - start_age)) * u(t - start_age)
    return value_func

# Net equity from house (market value - loan balance)
def house_equity_value(C, D, rate, term_years, appreciation, start_age):
    L = C - D 
    
    def equity_func(t):
        if t < start_age:
            return 0.0
        
        # Calculate total payments made so far using recurring_inflow
        total_payments = recurring_inflow(calculate_monthly_payment(L, rate, term_years), start_age, start_age + term_years, t, interval=1/12)
        
        # Calculate remaining loan balance
        loan_balance = L - total_payments
        
        # After loan term, balance is 0
        if t >= start_age + term_years:
            loan_balance = 0

        market_value = asset_value(C, appreciation, start_age)(t)
        return market_value - loan_balance
    return equity_func


def car_equity_value(C, D, rate, term_years, depreciation, start_age):
    L = C - D
    r_m = rate / 12
    N = term_years * 12
    
    def equity_func(t):
        if t < start_age:
            return 0.0
        months_elapsed = int((t - start_age) * 12)
        if months_elapsed >= N:
            loan_balance = 0
        else:
            loan_balance = L * ((1 + r_m) ** N - (1 + r_m) ** months_elapsed) / ((1 + r_m) ** N - 1)
        market_value = asset_value(C, depreciation, start_age)(t)
        return market_value - loan_balance
    return equity_func

# A hard reset that applies an inflow of money and disregards the rest of the envelope
def hard_reset(a, t_start, t):
    return a * u(t - t_start)

# def house_equity_value(C, D, rate, term_years, appreciation, start_age):
#     L = C - D
#     r_m = rate / 12
#     N = term_years * 12

#     def equity_func(t):
#         if t < start_age:
#             return 0.0
#         months_elapsed = int((t - start_age) * 12)
#         if months_elapsed >= N:
#             loan_balance = 0
#         else:
#             loan_balance = L * ((1 + r_m) ** N - (1 + r_m) ** months_elapsed) / ((1 + r_m) ** N - 1)

#         market_value = asset_value(C, appreciation, start_age)(t)
#         return market_value - loan_balance
#     return equity_func


# Define list of envelopes
envelopes = {
    'W1': [],       # cash
    'W2': [],       # investment
    'House': [],    # house equity
    'Car': [],      # car equity
}


# Add events to envelopes
envelopes['W1'].append(lambda t: recurring_inflow(10000, 1, 10, t))  # childhood income
envelopes['W1'].append(lambda t: outflow(500, 12, t))               # spending

#hard set money at 20 years old in cash to be 21000
# envelopes['W1'].append(lambda t: hard_reset(21000, 17, t))
# envelopes['W1'].append(lambda t: recurring_outflow(10000, 1, 10, t)*u(t-17))  # reverse the previous outflow
# envelopes['W1'].append(lambda t: inflow(500, 12, t)*u(t-17))               # reverse the previous outflow

envelopes['W1'].append(lambda t: outflow(5000, 10, t))              # investment
envelopes['W1'].append(lambda t: recurring_inflow(60000, 20, 60, t))          # Job Income
envelopes['W1'].append(lambda t: recurring_outflow(20000, 20, 60, t))         # Invest from cash
envelopes['W2'].append(lambda t: recurring_inflow(20000, 20, 60, t))  # Investing
# envelopes['W2'].append(lambda t: invest_inflow(5000, 10, t))          # Investment growth
envelopes['W2'].append(lambda t: recurring_outflow_compound_interest(10000, 65, 105, t))  # retirement from investment
envelopes['W1'].append(lambda t: recurring_outflow_compound_interest(20000, 65, 105, t))  # retirement from cash

# Parameters for mortgage and car loan
mortgage_rate = 0.06
mortgage_term = 30
mortgage_start_age = 25
house_value = 300000
house_down = 60000
house_appreciation = 0.01

envelopes['W1'].append(lambda t: outflow(house_down, mortgage_start_age, t))  # downpayment
envelopes['W1'].append(recurring_loan_outflow(house_value, house_down, mortgage_rate, mortgage_term, mortgage_start_age))  # mortgage outflow
envelopes['House'].append(house_equity_value(house_value, house_down, mortgage_rate, mortgage_term, house_appreciation, mortgage_start_age))  # net equity over time

envelopes['W1'].append(lambda t: recurring_outflow(5000, 20, 60, t))          # Rent



car_rate = 0.07
car_term = 5
car_start_age = 30
car_value = 40000
car_down = 5000
car_depreciation = -0.05


envelopes['W1'].append(lambda t: outflow(car_down, car_start_age, t))         # car downpayment
envelopes['W1'].append(recurring_loan_outflow(car_value, car_down, car_rate, car_term, car_start_age))  # car loan outflow
envelopes['Car'].append(car_equity_value(car_value, car_down, car_rate, car_term, car_depreciation, car_start_age))  # depreciating car value


if __name__ == "__main__":
    # Evaluate envelopes over time
    results = {}
    for key in envelopes:
        results[key] = np.zeros_like(t_range)
        for func in envelopes[key]:
            results[key] += np.array([func(t) for t in t_range])

    # Sum of all envelopes
    W_total = sum(results.values())

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.stackplot(t_range, results['W1'], results['W2'], results['House'], results['Car'],
                labels=['Cash (W1)', 'Investment (W2)', 'House Equity', 'Car Equity'])
    plt.plot(t_range, W_total, color='black', linestyle='--', label='Total Net Worth')
    plt.title('Net Worth Composition Including Modular House and Car Loans')
    plt.xlabel('Age (years)')
    plt.ylabel('Value ($)')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
