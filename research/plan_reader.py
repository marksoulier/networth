# Parse the json and implement the funtions.

import json
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Callable
from events_library.base_functions import u, R, evaluate_results, add_correction
from events_library.morgage_functions import buy_house, sell_house_and_transfer, change_payment, sell_home, create_home_value_function
from events_library.income_functions import get_a_job, start_business, business_income, business_loss, start_retirement
from events_library.expense_functions import add_living_expenses, add_rent_payment, buy_car, buy_boat, take_vacation, furnish_home
from events_library.insurance_functions import buy_health_insurance, medical_expense, buy_life_insurance, insurance_payout
from events_library.system_functions import take_net_worth_snapshot, manual_correction, apply_inflation
from events_library.show_visual import show_visual

@dataclass
class EventParameter:
    id: int
    type: str
    value: float

@dataclass
class Event:
    id: int
    type: str
    description: str
    parameters: List[EventParameter]
    updating_events: List['Event'] = None

def load_plan(plan_path: str) -> tuple[Dict[str, List], int]:
    """Load and parse the financial plan JSON file."""
    with open(plan_path, 'r') as f:
        data = json.load(f)
        current_time_days = data['current_time_days']
        
        # Initialize envelopes
        envelopes = {
            'W1': [],  # Cash
            'House': []  # House equity
        }
        
        # Process each event
        for event_data in data['events']:
            parameters = [
                EventParameter(
                    id=p['id'],
                    type=p['type'],
                    value=p['value']
                ) for p in event_data['parameters']
            ]
            
            # Create updating events if they exist
            updating_events = None
            if 'updating_events' in event_data:
                updating_events = []
                for update_data in event_data['updating_events']:
                    update_params = [
                        EventParameter(
                            id=p['id'],
                            type=p['type'],
                            value=p['value']
                        ) for p in update_data['parameters']
                    ]
                    updating_events.append(Event(
                        id=update_data['id'],
                        type=update_data['type'],
                        description=update_data['description'],
                        parameters=update_params
                    ))
            
            event = Event(
                id=event_data['id'],
                type=event_data['type'],
                description=event_data['description'],
                parameters=parameters,
                updating_events=updating_events
            )
            
            # Apply the event
            apply_event(event, envelopes)
        
        #print all the events with their parameters and updating events with their parameters in condense way
        print("Events:")
        for event in data['events']:
            print(f"Event {event['id']}: {event['type']} - {event['description']}")
            for param in event['parameters']:
                print(f"  {param['type']}: {param['value']}")
            if 'updating_events' in event:
                print("  Updating Events:")
                for update_event in event['updating_events']:
                    print(f"    {update_event['type']} - {update_event['description']}")
                    for param in update_event['parameters']:
                        print(f"      {param['type']}: {param['value']}")
        
        return envelopes, current_time_days

def get_parameter_value(parameters: List[EventParameter], param_type: str) -> float:
    """Helper method to get a parameter value by type."""
    for param in parameters:
        if param.type == param_type:
            return param.value
    return None

def apply_event(event: Event, envelopes: Dict[str, List]) -> None:
    """Apply a single event based on its type."""
    match event.type:
        case 'get_job':
            salary = get_parameter_value(event.parameters, 'salary')
            time_days = get_parameter_value(event.parameters, 'time_days')
            get_a_job(
                envelopes=envelopes,
                to_key='W1',
                salary=salary,
                pay_period=26,  # bi-weekly
                start_time=time_days,
                end_time=time_days + (20 * 365)  # 20 years from start
            )
        
        case 'cash_reset':
            amount = get_parameter_value(event.parameters, 'amount')
            time_days = get_parameter_value(event.parameters, 'time_days')
            add_correction(envelopes, tx=time_days, vactual=amount, envelope_key='W1')
        
        case 'buy_house':
            home_value = get_parameter_value(event.parameters, 'home_value')
            loan_term = get_parameter_value(event.parameters, 'loan_term_years')
            loan_rate = get_parameter_value(event.parameters, 'loan_rate')
            appreciation_rate = get_parameter_value(event.parameters, 'appreciation_rate')
            downpayment = get_parameter_value(event.parameters, 'downpayment')
            time_days = get_parameter_value(event.parameters, 'time_days')
            
            # Create home value function
            home_value_changes = []
            payment_changes = []
            
            if event.updating_events:
                for update_event in event.updating_events:
                    match update_event.type:
                        case 'new_appraisal':
                            print("new appraisal")
                            appraised_value = get_parameter_value(update_event.parameters, 'appraised_value')
                            update_time = get_parameter_value(update_event.parameters, 'time_days')
                            home_value_changes.append((update_time, appraised_value))
                        case 'sell_house':
                            print("sell house")
                            sell_time = get_parameter_value(update_event.parameters, 'time_days')
                            sell_home(home_value_changes, sell_time)                        
                        case 'change_payment':
                            print("change payment")
                            amount = get_parameter_value(update_event.parameters, 'amount')
                            update_time = get_parameter_value(update_event.parameters, 'time_days')
                            month_index = get_parameter_value(update_event.parameters, 'month_index')
                            payment_changes.append((month_index, update_time, amount))
            
            home_params = create_home_value_function(
                initial_value=home_value,
                initial_time=time_days,
                value_changes=home_value_changes
            )
            
            buy_house(
                envelopes=envelopes,
                start_time=time_days,
                downpayment=home_value * downpayment,
                annual_rate=loan_rate,
                years=loan_term,
                appreciation_rate=appreciation_rate,
                payment_changes=payment_changes,
                params_func=home_params
            )
            
            #check if sell house, then use it as it has to have the functions from the buy house to evalute the sell price
            if event.updating_events:
                for update_event in event.updating_events:
                    if update_event.type == 'sell_house':
                        sell_time = get_parameter_value(update_event.parameters, 'time_days')
                        sell_house_and_transfer(envelopes, from_key='House', to_key='W1', time_days=sell_time)

def read_plan(plan_file: str) -> Dict[str, List[Callable]]:
    """
    Read a financial plan from a JSON file and convert it to a dictionary of envelope functions.
    
    Parameters:
        plan_file: Path to the JSON plan file
        
    Returns:
        Dictionary mapping envelope names to lists of functions
    """
    with open(plan_file, 'r') as f:
        plan = json.load(f)
    
    # Initialize envelopes dictionary
    envelopes = {}
    for envelope in plan['envelopes']:
        envelopes[envelope] = []
    
    # Process each event
    for event in plan['events']:
        event_type = event['type']
        params = event['parameters']
        time_days = params.get('time_days', 0)
        
        # Map event types to their handler functions
        event_handlers = {
            'get_a_job': get_a_job,
            'start_business': start_business,
            'business_income': business_income,
            'business_loss': business_loss,
            'start_retirement': start_retirement,
            'add_living_expenses': add_living_expenses,
            'add_rent_payment': add_rent_payment,
            'buy_car': buy_car,
            'buy_boat': buy_boat,
            'take_vacation': take_vacation,
            'furnish_home': furnish_home,
            'buy_health_insurance': buy_health_insurance,
            'medical_expense': medical_expense,
            'buy_life_insurance': buy_life_insurance,
            'insurance_payout': insurance_payout,
            'take_net_worth_snapshot': take_net_worth_snapshot,
            'manual_correction': manual_correction,
            'apply_inflation': apply_inflation
        }
        
        # Call the appropriate handler function
        if event_type in event_handlers:
            handler = event_handlers[event_type]
            handler(envelopes, **params)
        
        # Process updating events
        for updating_event in event.get('updating_events', []):
            updating_type = updating_event['type']
            updating_params = updating_event['parameters']
            
            if updating_type in event_handlers:
                handler = event_handlers[updating_type]
                handler(envelopes, **updating_params)
    
    return envelopes

def main():
    # Load the plan and get envelopes
    envelopes = read_plan('financial_plan.json')
    
    # Evaluate results with inflation adjustment
    results = evaluate_results(
        envelopes=envelopes,
        start_day=0,
        end_day=365 * 20,  # 20 years
        frequency=30,  # Monthly points
        current_day=0,
        inflation_rate=0.03  # 3% annual inflation rate
    )
    
    # Show results
    show_visual(results, results['time'])

if __name__ == '__main__':
    main()

