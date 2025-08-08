from planner4 import T, R, P, f_in, f_out, f_salary, f_principal, gamma
import numpy as np

###########################################################
# Test Examples for Transferring Between Accounts
###########################################################

# Example 1: Simple transfer of $10,000 from cash to investment, start with 20,000
# Cash: No growth (0% rate)
# Investment: 6% yearly compound growth
example1_transfer = {
    "cash": {
        "functions": [
            T({"t_k": 365}, f_out, P({
                "b": 10000,  # Outflow from cash
            }), {"type": "Yearly Compound", "r": 0.00}),
            T({"t_k": 0}, f_in, P({
                "a": 20000,  # Start with 20,000
            }), {"type": "Yearly Compound", "r": 0.00})
        ]
    },
    "investment": {
        "functions": [
            T({"t_k": 365}, f_in, P({
                "a": 10000,  # Inflow to investment
            }), {"type": "Yearly Compound", "r": 0.06})
        ]
    }
}

# Example 2: Monthly transfer of $500 from salary to 401k
# Salary: Weekly payments with tax deductions
# 401k: 7% yearly compound growth
example2_monthly_transfer = {
    "cash": {
        "functions": [
            # Salary income
            R({"t0": 0, "dt": 7, "tf": 10*365}, f_salary, P({
                "S": 70000, "p": 52,
                "r_SS": 0.062, "r_Med": 0.0145,
                "r_Fed": 0.12, "r_401k": 0.06
            }), {"type": "Yearly Compound", "r": 0.07}),
            # Monthly transfer out
            R({"t0": 30, "dt": 30.42, "tf": 10*365}, f_out, P({
                "b": 500,  # Monthly transfer out
            }), {"type": "Yearly Compound", "r": 0.07})
        ]
    },
    "401k": {
        "functions": [
            # Monthly transfer in with growth
            R({"t0": 30, "dt": 30.42, "tf": 10*365}, f_in, P({
                "a": 500,  # Monthly transfer in
            }), {"type": "Yearly Compound", "r": 0.07})
        ]
    }
}

# Example 3: Transfer with different growth types
# Savings: 4% daily compound (high-yield savings)
# Investment: 8% yearly compound (stock market)
example3_growth_types = {
    "savings": {
        "functions": [
            # Initial deposit
            T({"t_k": 0}, f_in, P({
                "a": 50000,  # Initial deposit
            }), {"type": "Yearly Compound", "r": 0.08}),
            # Transfer out after 2 years
            T({"t_k": 2*365}, f_out, P({
                "b": 25000,  # Transfer out
            }), {"type": "Yearly Compound", "r": 0.08})
        ]
    },
    "investment": {
        "functions": [
            # Transfer in after 2 years
            T({"t_k": 2*365}, f_in, P({
                "a": 25000,  # Transfer in
            }), {"type": "Yearly Compound", "r": 0.08})
        ]
    }
}

# Example 5: Gamma salary change - salary increases during job
# Start at $60k, raise to $75k at year 3, then to $90k at year 6
example5_gamma_salary = {
    "cash": {
        "functions": [
            # Base salary with gamma overrides for raises
            R({"t0": 0, "dt": 7, "tf": 10*365}, f_salary, gamma(
                gamma(
                    P({
                        "S": 60000, "p": 52,
                        "r_SS": 0.062, "r_Med": 0.0145,
                        "r_Fed": 0.12, "r_401k": 0.06
                    }),
                    {"S": 75000},  # First raise
                    3*365  # At year 3
                ),
                {"S": 90000},  # Second raise
                6*365  # At year 6
            ), {"type": "Yearly Compound", "r": 0.07})
        ]
    }
}

example6_house_purchase = {
    "cash": {
        "functions": [
            # Initial cash
            T({"t_k": 0}, f_in, P({
                "a": 100000,  # Start with 100k cash
            }), {"type": "None", "r": 0.0}),
            # Recurring salary income
            R({"t0": 0, "dt": 14, "tf": 35*365}, f_salary, P({
                "S": 50000, "p": 26,  # Bi-weekly pay
                "r_SS": 0.062, "r_Med": 0.0145,
                "r_Fed": 0.12, "r_401k": 0.06
            }), {"type": "None", "r": 0.0}),
            # Down payment outflow when buying house
            T({"t_k": 365}, f_out, P({
                "b": 40000,  # 40k down payment
            }), {"type": "None", "r": 0.0})
        ]
    },
    "home": {
        "functions": [
            # House purchase with appreciation growth
            T({"t_k": 365}, f_in, P({
                "a": 200000,  # House value 200k
            }), {"type": "Appreciation", "r": 0.03})  # 3% annual appreciation
        ]
    },
    "home_mortgage": {
        "functions": [
            # Loan amount outflow from mortgage envelope (house value - down payment)
            T({"t_k": 365}, f_out, P({
                "b": 160000,  # Loan amount (200k - 40k down)
            }), {"type": "None", "r": 0.0}),
            # Monthly mortgage payments (principal + interest)
            R({"t0": 365, "dt": 365/12, "tf": 31*365}, f_principal, P({
                "P": 160000,  # Loan amount (200k - 40k down)
                "r": 0.045,   # 4.5% annual rate
                "y": 30       # 30 year loan
            }), {"type": "None", "r": 0.0})
        ]
    }
}

# Updated list with all examples
transfer_examples = [
    # example1_transfer,
    # example2_monthly_transfer,
    # example3_growth_types,
    # example5_gamma_salary,
    example6_house_purchase,
]

# For analysis - use existing evaluate_results function
from base_functions import evaluate_results, show_visual

t_end = 35*365
interval = 10
t_range = np.arange(0, t_end, interval)

for example in transfer_examples:
    results = evaluate_results(example, 0, t_end, interval)
    show_visual(results, t_range) 