import numpy as np
from dataclasses import dataclass
from typing import List, Callable, Dict, Tuple, Optional
from events_library.job_functions import get_a_job
from events_library.morgage_functions import (
    buy_house, sell_house, create_home_value_function,
    sell_house_and_transfer, new_appraisal, sell_home, change_payment
)
from events_library.base_functions import add_correction, u, inflation_adjust, evaluate_results
from events_library.show_visual import show_visual

# Example usage
if __name__ == "__main__":
    # Initialize envelopes
    envelopes = {
        'W1': [],  # Cash
        'House': []  # House equity
    }
    
    # Get job at year 0
    get_a_job(envelopes, to_key='W1', salary=50000, pay_period=14, start_time=0, end_time=20 * 365)  # $50,000/year, bi-weekly pay for 20 years
    
    # Define all home value changes
    home_value_changes = []
    
    # Add appraisals and sale
    new_appraisal(home_value_changes, 5 * 365, 450000)  # Year 5: Value increases to $450,000
    sell_home(home_value_changes, 15 * 365)  # Year 15: Sell the house
    
    # Create complete home value function
    home_params = create_home_value_function(
        initial_value=300000,
        initial_time=2 * 365,  # Buy at year 2
        value_changes=home_value_changes
    )
    
    # Define payment changes
    payment_changes = []
    
    # Add payment changes
    change_payment(payment_changes, 84, 7 * 365 + (365/12), 2000)  # Year 7, month 1: Pay a month late
    change_payment(payment_changes, 120, 10 * 365, 50000)  # Year 10: Extra $50,000 payment
    
    # Buy house at year 2
    buy_house(
        envelopes=envelopes,
        start_time=2 * 365,  # Buy house at year 2
        downpayment=60000,   # 20% down payment
        annual_rate=0.03,    # 3% interest rate
        years=30,
        appreciation_rate=0.05,  # 5% appreciation
        payment_changes=payment_changes,
        params_func=home_params
    )
    
    # Sell house at year 15
    sell_house_and_transfer(envelopes, from_key='House', to_key='W1', time_days=15 * 365 - 1)
    
    # Change bank balance, corrections need to be done after functions are applied
    add_correction(envelopes, tx=3 * 365, vactual=135000, envelope_key='W1')
    
    # Evaluate results with inflation adjustment
    t_range = np.arange(0, 365 * 20, 10)
    results = evaluate_results(
        envelopes=envelopes,
        start_day=0,
        end_day=365 * 20,
        frequency=10,
        current_day=4380,  # 12 years from start
        inflation_rate=0.03  # 3% annual inflation rate
    )
    
    # Show results
    show_visual(results, t_range)