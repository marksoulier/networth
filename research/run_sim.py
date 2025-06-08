import json
from pprint import pprint
from events_library.schema_checker import extract_schema, validate_problem, parse_events
from events_library.planner3 import evaluate_results, show_visual, get_job
import numpy as np

def initialize_envelopes():
    """Initialize empty envelopes dictionary with common financial categories"""
    return {
        "Cash": [],
    }

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
    envelopes = initialize_envelopes()
    
    # Process each event
    for event in parsed_events:
        event_type = event["type"]
        # Apply the event function to the envelopes
        if event_type == "get_job":
            get_job(event, envelopes)
        # Add more event type handlers here as needed
        # elif event_type == "buy_house":
        #     buy_house(event, envelopes)
        # etc...

    # Set up simulation parameters
    t_end = 20*365  # 20 years
    interval = 5    # 5-day intervals
    t_range = np.arange(0, t_end, interval)

    # Evaluate and display results
    results = evaluate_results(envelopes, 0, t_end, interval)
    show_visual(results, t_range)

if __name__ == "__main__":
    # Example plan and schema paths
    plan_path = "events_library/plan.json"
    schema_path = "events_library/event_schema.json"
    run_simulation(plan_path, schema_path)
