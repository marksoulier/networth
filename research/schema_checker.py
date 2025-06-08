def extract_schema(schema):
    event_schemas = {}
    for event in schema["events"]:
        print(event["type"])
        event_type = event["type"]
        params = {p["type"] for p in event["parameters"]}
        event_schemas[event_type] = {"params": params, "updating_events": {}}

        # handle nested updating events
        if "updating_events" in event:
            for update in event["updating_events"]:
                update_type = update["type"]
                update_params = {p["type"] for p in update["parameters"]}
                event_schemas[event_type]["updating_events"][update_type] = update_params
    return event_schemas

def validate_parameters(event_type, event_id, expected_params, provided_params, is_updating=False, parent_event_id=None):
    """Helper function to validate parameters for both regular and updating events"""
    errors = []
    
    # Convert provided parameters to set of types
    provided_param_types = set()
    for param in provided_params:
        param_type = param.get("type")
        if param_type:
            provided_param_types.add(param_type)

    # Check for missing parameters
    missing_params = expected_params - provided_param_types
    if missing_params:
        event_desc = f"{event_type} under {parent_event_id}" if is_updating else event_type
        errors.append(f"❌ Missing in {event_desc}: {missing_params}")

    # Check for extra parameters
    extra_params = provided_param_types - expected_params
    if extra_params:
        event_desc = f"updating event {event_type}, parent event {parent_event_id}" if is_updating else f"event {event_id} ({event_type})"
        errors.append(f"❌ Unexpected parameters in {event_desc}: {extra_params}")

    # Check for duplicate parameter IDs
    param_ids = [p.get("id") for p in provided_params]
    duplicates = {x for x in param_ids if param_ids.count(x) > 1}
    if duplicates:
        event_desc = f"updating event {event_type}, parent event {parent_event_id}" if is_updating else f"event {event_id} ({event_type})"
        errors.append(f"❌ Duplicate parameter ids in {event_desc}: {duplicates}")

    return errors

def validate_event_ids(events, is_updating=False, parent_event_id=None):
    """Helper function to validate event IDs for both regular and updating events"""
    errors = []
    seen_ids = set()
    
    for event in events:
        event_id = event.get("id")
        if event_id in seen_ids:
            event_desc = f"updating event id in event {parent_event_id}" if is_updating else "event id"
            errors.append(f"❌ Duplicate {event_desc}: {event_id}")
        else:
            seen_ids.add(event_id)
            
    return errors

def validate_problem(problem, schema_map):
    errors = []
    seen_event_ids = set()

    for event in problem["events"]:
        event_type = event["type"]
        if event_type not in schema_map:
            errors.append(f"❌ Unknown event type: {event_type}")
            continue

        # Validate main event parameters
        event_id = event.get("id")
        errors.extend(validate_parameters(
            event_type=event_type,
            event_id=event_id,
            expected_params=schema_map[event_type]["params"],
            provided_params=event.get("parameters", []),
            is_updating=False
        ))

        # Validate main event IDs
        if event_id in seen_event_ids:
            errors.append(f"❌ Duplicate event id: {event_id}")
        else:
            seen_event_ids.add(event_id)

        # Validate updating events
        if "updating_events" in event:
            for update_event in event["updating_events"]:
                update_type = update_event["type"]
                if update_type not in schema_map[event_type]["updating_events"]:
                    errors.append(f"❌ Unknown updating event type: {update_type} under {event_type}")
                    continue

                # Validate updating event parameters
                errors.extend(validate_parameters(
                    event_type=update_type,
                    event_id=update_event.get("id"),
                    expected_params=schema_map[event_type]["updating_events"][update_type],
                    provided_params=update_event.get("parameters", []),
                    is_updating=True,
                    parent_event_id=event_id
                ))

            # Validate updating event IDs
            errors.extend(validate_event_ids(
                events=event["updating_events"],
                is_updating=True,
                parent_event_id=event_id
            ))

    return errors

import json

# Example usage:
# schema_dict = json.load(open("event_schema.json"))
# problem_dict = json.load(open("plan.json"))
# schema_map = extract_schema(schema_dict)
# issues = validate_problem(problem_dict, schema_map)
# for issue in issues:
#     print(issue)



def parse_events(problem_dict):
    parsed = []

    for event in problem_dict.get("events", []):
        base_event = {
            "id": event.get("id"),
            "type": event.get("type"),
            "description": event.get("description", ""),
            "parameters": {p["type"]: p["value"] for p in event.get("parameters", [])},
            "updating_events": []
        }

        for upd in event.get("updating_events", []):
            update = {
                "id": upd.get("id"),
                "type": upd.get("type"),
                "description": upd.get("description", ""),
                "parameters": {p["type"]: p["value"] for p in upd.get("parameters", [])}
            }
            base_event["updating_events"].append(update)

        parsed.append(base_event)

    return parsed

# parsed = parse_events(problem_dict)
# from pprint import pprint
# pprint(parsed)



