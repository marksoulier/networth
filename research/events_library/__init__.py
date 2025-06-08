"""
Events library for financial planning.
This package contains modules for handling various types of financial events.
"""

from .base_functions import u, R
from .morgage_functions import buy_house
from .income_functions import get_a_job, start_business, business_income, business_loss, start_retirement
from .expense_functions import add_living_expenses, add_rent_payment, buy_car, buy_boat, take_vacation, furnish_home
from .insurance_functions import buy_health_insurance, medical_expense, buy_life_insurance, insurance_payout
from .system_functions import take_net_worth_snapshot, manual_correction, apply_inflation

__all__ = [
    'u', 'R',
    'buy_house',
    'get_a_job', 'start_business', 'business_income', 'business_loss', 'start_retirement',
    'add_living_expenses', 'add_rent_payment', 'buy_car', 'buy_boat', 'take_vacation', 'furnish_home',
    'buy_health_insurance', 'medical_expense', 'buy_life_insurance', 'insurance_payout',
    'take_net_worth_snapshot', 'manual_correction', 'apply_inflation'
] 