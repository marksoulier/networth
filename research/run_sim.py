import json
from pprint import pprint
from schema_checker import extract_schema, validate_problem, parse_events

from planner4 import (manual_correction, transfer_money,
    reoccuring_income, reoccuring_spending, reoccuring_transfer,
    get_job, purchase, gift, start_business, retirement, buy_house,
    buy_car, have_kid, marriage, divorce, pass_away,
    buy_health_insurance, buy_life_insurance,
    receive_government_aid, invest_money, high_yield_savings_account,
    pay_taxes, buy_groceries, get_wage_job
)
from base_functions import evaluate_results, show_visual
import numpy as np

def initialize_envelopes(problem_dict):
    """Initialize envelopes as a dict with keys for each envelope name, each containing 'functions' and 'growth'.
    The 'growth' function takes theta (a function of t_i), t, t_i and returns the value using the correct compounding logic.
    """
    envelopes = {}
    for env in problem_dict["envelopes"]:
        name = env["name"]
        growth_type = env.get("growth", "None")
        rate = env.get("rate", 0.0)
        envelopes[name] = {"functions": [], "growth_type": growth_type, "growth_rate": rate}
    return envelopes
    

def run_simulation(plan_path: str, schema_path: str):
    # Load and validate the plan and schema
    with open(schema_path, 'r') as f:
        schema_dict = json.load(f)
    with open(plan_path, 'r') as f:
        problem_dict = json.load(f)

    # Validate the plan against schema
    schema_map = extract_schema(schema_dict)
    issues = validate_problem(problem_dict, schema_map)
    
    if issues:
        print("❌ Validation issues found:")
        for issue in issues:
            print(issue)
        return

    # Parse events into a more usable format
    parsed_events = parse_events(problem_dict)
    pprint(parsed_events)

    # Initialize empty envelopes
    envelopes = initialize_envelopes(problem_dict)
    
    for event in parsed_events:
        event_type = event["type"]

        if event_type == "purchase":
            purchase(event, envelopes)

        elif event_type == "gift":
            gift(event, envelopes)

        elif event_type == "get_job":
            get_job(event, envelopes)
        
        elif event_type == "get_wage_job":
            get_wage_job(event, envelopes)

        elif event_type == "start_business":
            start_business(event, envelopes)

        elif event_type == "retirement":
            retirement(event, envelopes)
        
        elif event_type == "buy_house":
            buy_house(event, envelopes)

        elif event_type == "buy_car":
            buy_car(event, envelopes)

        elif event_type == "have_kid":
            have_kid(event, envelopes)

        elif event_type == "marriage":
            marriage(event, envelopes)

        elif event_type == "divorce":
            divorce(event, envelopes)

        elif event_type == "buy_health_insurance":
            buy_health_insurance(event, envelopes)

        elif event_type == "buy_life_insurance":
            buy_life_insurance(event, envelopes)

        elif event_type == "receive_government_aid":
            receive_government_aid(event, envelopes)

        elif event_type == "invest_money":
            invest_money(event, envelopes)

        elif event_type == "high_yield_savings_account":
            high_yield_savings_account(event, envelopes)

        elif event_type == "pay_taxes":
            pay_taxes(event, envelopes)

        elif event_type == "buy_groceries":
            buy_groceries(event, envelopes)

        elif event_type == "manual_correction":
            manual_correction(event, envelopes)
        
        elif event_type == "transfer_money":
            transfer_money(event, envelopes)
            
        elif event_type == "pass_away":
            pass_away(event, envelopes)
            
        elif event_type == "reoccuring_income":
            reoccuring_income(event, envelopes)
            
        elif event_type == "reoccuring_spending":
            reoccuring_spending(event, envelopes)
            
        elif event_type == "reoccuring_transfer":
            reoccuring_transfer(event, envelopes)
        else:
            print(f"⚠️ Unhandled event type: {event_type}")

    # Set up simulation parameters
    t_end = 30*365  # 20 years
    interval = 5    # 5-day intervals
    t_range = np.arange(0, t_end, interval)

    # Evaluate and display results
    results = evaluate_results(envelopes, 0, t_end, interval)
    show_visual(results, t_range)

if __name__ == "__main__":
    # Example plan and schema paths
    plan_path = "plan6.json"
    schema_path = "event_schema.json"
    run_simulation(plan_path, schema_path)
