from typing import Dict, Any, Callable


def u(t: float) -> float:
    return 1.0 if t >= 0 else 0.0

def P(params: Dict[str, Any]) -> Callable[[float], Dict[str, Any]]:
    """Convert a dictionary of parameters into a time-varying parameter function.
    The returned function will always return the same parameters regardless of time."""
    return lambda t: params

# θ_inf = {"r_inf": inflation_rate, "t_today": reference_day}
def f_inflation_adjust(W: Callable[[float], float], theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: W(t) / ((1 + params["r_inf"]) ** ((t - params["t_today"]) / 365)) if t >= params["t_today"] else W(t)

# Parameter Override Function: γ(θ, θ_change, t*)
def gamma(theta: Callable[[float], Dict[str, float]], theta_change: Dict[str, float], t_star: float) -> Callable[[float], Dict[str, float]]:
    """Parameter override function that changes parameters at time t_star"""
    def theta_t(t: float) -> Dict[str, float]:
        if t < t_star:
            return theta(t)
        else:
            return {**theta(t), **theta_change}
    return theta_t

# Occurrence: T(θ_event, f, θ(t), θ_g, t)
# θ_event = {"t_k": event_time}
def T(theta_event: Dict[str, float], f: Callable[[Dict[str, float]], float], 
      theta: Callable[[float], Dict[str, float]], theta_g: Dict[str, Any]) -> Callable[[float], float]:
    """Occurrence function - single event at time t_k with growth"""
    t_k = theta_event['t_k']
    params = theta(t_k)  # θ = θ(t_k) - evaluate at t_k
    return lambda t: f(params, t_k) * u(t - t_k) * f_growth(theta_g, t - t_k)

# θ_re = {t_0, dt, t_f}
def R(theta_re: Dict[str, float], f: Callable[[Dict[str, float], float], float], 
      theta: Callable[[float], Dict[str, float]], theta_g: Dict[str, Any], omega: Dict[int, tuple] = {}) -> Callable[[float], float]:
    """Recurring function with overrides in Ω and growth"""
    t0 = theta_re["t0"]
    dt = theta_re["dt"]
    tf = theta_re["tf"]
    
    def recurring_func(t: float) -> float:
        total = 0.0
        i = 0
        while True:
            ti = t0 + i * dt
            if ti > tf:
                break
                
            # Check if there's an override for this index
            if i in omega:
                t_hat, theta_prime = omega[i]
                current_t = t_hat
                current_theta = theta_prime
            else:
                current_t = ti
                current_theta = theta
            
            # Apply the occurrence function with growth
            occurrence = T({"t_k": current_t}, f, current_theta, theta_g)
            total += occurrence(t)
            i += 1
            
        return total
    
    return recurring_func

# θ_g = {"type": growth_type, "r": rate}
def f_growth(theta_g: Dict[str, Any], t: float) -> float:
    """Growth magnitude function with different compounding types"""
    growth_type = theta_g["type"]
    r = theta_g["r"]
    
    if growth_type == "Daily Compound":
        return (1 + r/365) ** (365 * t/365)
    elif growth_type == "Monthly Compound":
        return (1 + r/12) ** (12 * t/365)
    elif growth_type == "Yearly Compound":
        return (1 + r) ** (t/365)
    elif growth_type == "Simple Interest":
        return 1 + r * (t/365)
    elif growth_type == "Appreciation":
        return 1 + r * (t/365)
    elif growth_type == "Depreciation":
        return 1 - r * (t/365)
    elif growth_type == "None":
        return 1
    else:
        raise ValueError(f"Unknown growth type: {growth_type}")

# θ_obs = {"V_obs": observed_value, "t_k": observation_time}
def O_empirical(theta: Dict[str, float], t: float) -> float:
    """Empirical override function"""
    V_obs = theta["V_obs"]
    t_k = theta["t_k"]
    
    # Dirac delta approximation - returns V_obs when t is very close to t_k
    epsilon = 1e-6
    if abs(t - t_k) < epsilon:
        return V_obs
    else:
        return 0.0

# θ_in = {"a": inflow_amount}
def f_in(theta_in: Dict[str, float], t: float) -> float:
    """Inflow function: a"""
    return theta_in["a"]

# θ_out = {"b": outflow_amount}
def f_out(theta_out: Dict[str, float], t: float) -> float:
    """Outflow function: -b"""
    return -theta_out["b"]

# θ_s = {"S": salary, "p": pay_periods, "r_SS": social_security_rate, "r_Med": medicare_rate, "r_Fed": federal_tax_rate, "r_401k": retirement_rate}
def f_salary(theta_s: Dict[str, float], t: float) -> float:
    """Salary function with tax deductions: S/p * (1 - r_SS - r_Med - r_Fed - r_401k)"""
    S = theta_s["S"]  # Salary
    p = theta_s["p"]  # Pay periods per year
    r_SS = theta_s["r_SS"]  # Social Security rate
    r_Med = theta_s["r_Med"]  # Medicare rate
    r_Fed = theta_s["r_Fed"]  # Federal tax rate
    r_401k = theta_s["r_401k"]  # 401k contribution rate
    
    return (S / p) * (1 - r_SS - r_Med - r_Fed - r_401k)

# θ_w = {"w": hourly_wage, "h": hours_per_week, "p": pay_periods, "r_SS": social_security_rate, "r_Fed": federal_tax_rate, "r_Med": medicare_rate, "r_401k": retirement_rate}
def f_wage(theta_w: Dict[str, float], t: float) -> float:
    """Wage function with tax deductions: (w * h * 52) / p * (1 - r_SS - r_Fed - r_Med - r_401k)"""
    w = theta_w["w"]  # Hourly wage
    h = theta_w["h"]  # Hours per week
    p = theta_w["p"]  # Pay periods per year
    r_SS = theta_w["r_SS"]  # Social Security rate
    r_Fed = theta_w["r_Fed"]  # Federal tax rate
    r_Med = theta_w["r_Med"]  # Medicare rate
    r_401k = theta_w["r_401k"]  # 401k contribution rate
    
    return ((w * h * 52) / p) * (1 - r_SS - r_Fed - r_Med - r_401k)

# θ_401 = {"S": salary, "p": pay_periods, "r_401": 401k_contribution_rate}
def f_401(theta_401: Dict[str, float], t: float) -> float:
    """401(k) contribution function: S/p * r_401"""
    S = theta_401["S"]  # Salary
    p = theta_401["p"]  # Pay periods per year
    r_401 = theta_401["r_401"]  # 401k contribution rate
    
    return (S / p) * r_401

# θ_mortgage = {"P": principal, "r": annual_rate, "y": years}
def f_mortgage(theta: Dict[str, float], t: float) -> float:
    return theta["P"] * (theta["r"] / 12) * ((1 + theta["r"] / 12) ** (12 * theta["y"])) / (((1 + theta["r"] / 12) ** (12 * theta["y"])) - 1)

# θ_principal = {"P": loan_amount, "r": annual_rate, "y": years, "p_mortgage": fixed_monthly_payment}
def f_principal(theta: Dict[str, float], t: float) -> float:
    months = int(t / (365 / 12))
    r = theta["r"]
    y = theta["y"]
    Loan = theta["P"]
    # Calculate default mortgage payment if not provided
    default_payment = Loan * (r / 12) * ((1 + r / 12) ** (12 * y)) / (((1 + r / 12) ** (12 * y)) - 1)
    p_m = theta.get("p_mortgage", default_payment)
    payment = Loan * ((1 + r / 12) ** months) * (r / 12) / (((1 + r / 12) ** (12 * y)) - 1)
    mortgage_amt = f_mortgage({"P": Loan, "r": r, "y": y}, t)
    return payment + max(mortgage_amt - p_m, 0)

# θ_insurance = {"p0": base_premium, "r_adj": annual_rate}
def f_insurance(theta: Dict[str, float], t: float) -> float:
    """Insurance premium function with annual adjustment"""
    return theta["p0"] * (1 + theta["r_adj"]) ** (t / 365)

# θ_maint = {"m0": base_cost, "alpha": slope, "t0": start_time}
def f_maint(theta: Dict[str, float], t: float) -> float:
    """Maintenance cost function with linear growth"""
    return theta["m0"] + theta["alpha"] * (t - theta["t0"])

# θ_empirical = {"V_obs": observed_value, "t_k": observation_time}
def f_empirical(theta: Dict[str, float], t: float) -> float:
    """Empirical override function"""
    params = theta(t) if callable(theta) else theta
    V_obs = params["V_obs"]
    t_k = params["t_k"]
    
    # Dirac delta approximation - returns V_obs when t is very close to t_k
    epsilon = 1e-6
    if abs(t - t_k) < epsilon:
        return V_obs
    else:
        return 0.0
    
####################################
# Events
####################################

def get_growth_parameters(envelopes: dict, from_key: str = None, to_key: str = None) -> tuple:
    """Get growth parameters for source and destination envelopes.
    Returns a tuple of (theta_growth_source, theta_growth_destination) dictionaries."""
    
    # Get source growth parameters
    theta_growth_source = {"type": "None", "r": 0.0}
    if from_key and from_key in envelopes:
        source_env = envelopes[from_key]
        theta_growth_source = {
            "type": source_env.get("growth_type", "None"),
            "r": source_env.get("growth_rate", 0.0)
        }
    
    # Get destination growth parameters
    theta_growth_destination = {"type": "None", "r": 0.0}
    if to_key and to_key in envelopes:
        dest_env = envelopes[to_key]
        theta_growth_destination = {
            "type": dest_env.get("growth_type", "None"),
            "r": dest_env.get("growth_rate", 0.0)
        }
    
    return theta_growth_source, theta_growth_destination

def manual_correction(event: dict, envelopes: dict):
    """Handle manual corrections to envelope values with different behaviors based on account type."""
    params = event["parameters"]
    to_key = params["to_key"]
    env = envelopes[to_key]
    
    simulated_value = 0.0
    for func in env["functions"]:
        simulated_value += func(params["start_time"])
    difference = params["amount"] - simulated_value
    print("Difference applied:", difference)
    
    # Get growth parameters from envelope
    _, theta_growth_dest = get_growth_parameters(envelopes, to_key=to_key)
    
    # Create the correction function and append it to the envelope
    correction_func = T(
        {"t_k": params["start_time"]},
        f_in if difference > 0 else f_out,
        P({"a": abs(difference)} if difference > 0 else {"b": abs(difference)}),
        theta_growth_dest
    )
    env["functions"].append(correction_func)

def transfer_money(event: dict, envelopes: dict):
    """Transfer money between envelopes with optional growth rate for destination."""
    params = event["parameters"]
    
    # Get growth parameters for both envelopes
    theta_growth_source, theta_growth_dest = get_growth_parameters(
        envelopes, from_key=params["from_key"], to_key=params["to_key"]
    )
    
    # Create outflow function for source envelope
    outflow_func = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["amount"]}),
        theta_growth_source
    )
    envelopes[params["from_key"]]["functions"].append(outflow_func)
    
    # Create inflow function for destination envelope with growth
    inflow_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["amount"]}),
        theta_growth_dest
    )
    envelopes[params["to_key"]]["functions"].append(inflow_func)

def reoccuring_income(event: dict, envelopes: dict):
    """Handle recurring income events by adding recurring inflows to an envelope."""
    params = event["parameters"]
    
    # Get growth parameters for destination envelope
    _, theta_growth_dest = get_growth_parameters(envelopes, to_key=params["to_key"])
    
    # Create recurring income function
    income_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_days"]},
        f_in,
        P({"a": params["amount"]}),
        theta_growth_dest
    )
    
    envelopes[params["to_key"]]["functions"].append(income_func)

def reoccuring_spending(event: dict, envelopes: dict):
    """Handle recurring spending events by adding recurring outflows from an envelope."""
    params = event["parameters"]
    
    # Get growth parameters for source envelope
    theta_growth_source, _ = get_growth_parameters(envelopes, from_key=params["from_key"])
    
    # Create recurring spending function
    spending_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_days"]},
        f_out,
        P({"b": params["amount"]}),
        theta_growth_source
    )
    
    envelopes[params["from_key"]]["functions"].append(spending_func)

def reoccuring_transfer(event: dict, envelopes: dict):
    """Handle recurring transfer events by adding recurring outflows from one envelope and inflows to another."""
    params = event["parameters"]
    
    # Get growth parameters for both envelopes
    theta_growth_source, theta_growth_dest = get_growth_parameters(
        envelopes, from_key=params["from_key"], to_key=params["to_key"]
    )
    
    # Outflow from source envelope
    outflow_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_days"]},
        f_out,
        P({"b": params["amount"]}),
        theta_growth_source
    )
    
    envelopes[params["from_key"]]["functions"].append(outflow_func)
    
    # Inflow to destination envelope
    inflow_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_days"]},
        f_in,
        P({"a": params["amount"]}),
        theta_growth_dest
    )
    envelopes[params["to_key"]]["functions"].append(inflow_func)

####################################
# Migrated Events from planner3
####################################

def get_job(event: dict, envelopes: dict):
    """Handle a salary job event by adding salary payments and 401(k) contributions to specified envelopes."""
    params = event["parameters"]

    # Base job parameters dictionary for P(...)
    theta_base = {
        "S": params["salary"],
        "p": params["pay_period"],
        "r_Fed": params["federal_income_tax"],
        "r_SS": params["social_security_tax"],
        "r_Med": params["medicare_tax"],
        "r_401k": params["p_401k_contribution"],
        "r_state": params["state_income_tax"],
    }

    # Compose the base theta(t)
    theta = P(theta_base)

    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "get_a_raise":
            theta = gamma(theta, {"S": upd_params["salary"]}, upd_params["start_time"])

        elif upd_type == "change_401k_contribution":
            theta = gamma(theta, {"r_401k": upd_params["p_401k_contribution"]}, upd_params["start_time"])

        elif upd_type == "get_a_bonus":
            envelopes[params["to_key"]]["functions"].append(
                T({"t_k": upd_params["start_time"]}, f_in, P({"a": upd_params["bonus"]}), {"type": "None", "r": 0.0})
            )

    # Add salary payments to cash envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(
        R({"t0": params["start_time"], "dt": 365/params["pay_period"], "tf": params["end_time"]}, 
          f_salary, theta, {"type": "None", "r": 0.0})
    )

    # Add 401(k) contributions if specified
    contribution_amount = (params["salary"] / params["pay_period"]) * \
        (params["p_401k_contribution"] + params["p_401k_match"])
    
    # Get growth parameters from 401k envelope
    _, theta_growth_401k = get_growth_parameters(envelopes, to_key=params["p_401k_key"])
    
    envelopes[params["p_401k_key"]]["functions"].append(
        R({"t0": params["start_time"], "dt": 365/params["pay_period"], "tf": params["end_time"]}, 
          f_in, P({"a": contribution_amount}), theta_growth_401k)
    )

def get_wage_job(event: dict, envelopes: dict):
    """Handle a wage job event by adding wage payments and 401(k) contributions to specified envelopes."""
    params = event["parameters"]

    # Base wage parameters dictionary for P(...)
    theta_base = {
        "w": params["hourly_wage"],
        "h": params["hours_per_week"],
        "p": params["pay_period"],
        "r_Fed": params["federal_income_tax"],
        "r_SS": params["social_security_tax"],
        "r_Med": params["medicare_tax"],
        "r_401k": params["p_401k_contribution"],
        "r_match": params["employer_match"],
    }

    # Compose the base theta(t)
    theta = P(theta_base)

    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "get_a_raise":
            theta = gamma(theta, {"w": upd_params["new_hourly_wage"]}, upd_params["start_time"])

        elif upd_type == "change_hours":
            theta = gamma(theta, {"h": upd_params["new_hours"]}, upd_params["start_time"])

        elif upd_type == "change_401k_contribution":
            theta = gamma(theta, {"r_401k": upd_params["p_401k_contribution"]}, upd_params["start_time"])

        elif upd_type == "change_employer_match":
            theta = gamma(theta, {"r_match": upd_params["new_match_rate"]}, upd_params["start_time"])

    # Add wage payments to cash envelope
    cash_key = params["to_key"]
    envelopes[cash_key]["functions"].append(
        R({"t0": params["start_time"], "dt": 365/params["pay_period"], "tf": params["end_time"]}, 
          f_wage, theta, {"type": "None", "r": 0.0})
    )

    # Add 401(k) contributions if specified
    contribution_amount = (params["hourly_wage"] * params["hours_per_week"] * 52 / params["pay_period"]) * (params["p_401k_contribution"] + params["employer_match"])
    
    # Get growth parameters from 401k envelope
    _, theta_growth_401k = get_growth_parameters(envelopes, to_key=params["p_401k_key"])
    
    # Add 401(k) contributions
    envelopes[params["p_401k_key"]]["functions"].append(
        R({"t0": params["start_time"], "dt": 365/params["pay_period"], "tf": params["end_time"]}, 
          f_in, P({"a": contribution_amount}), theta_growth_401k)
    )

def purchase(event: dict, envelopes: dict):
    """Handle a purchase event by removing money from the specified envelope."""
    params = event["parameters"]    
    
    # Create a one-time outflow function for the purchase
    purchase_func = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["money"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add the purchase function to the specified envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(purchase_func)

def gift(event: dict, envelopes: dict):
    """Handle a gift event by adding money to the specified envelope."""
    params = event["parameters"]
    
    # Get growth parameters from destination envelope
    _, theta_growth_dest = get_growth_parameters(envelopes, to_key=params["to_key"])
    
    # Create a one-time inflow function for the gift
    gift_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["money"]}),
        theta_growth_dest
    )
    
    # Add the gift function to the specified envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(gift_func)

def start_business(event: dict, envelopes: dict):
    """Handle starting a business with initial investment and potential income/losses."""
    params = event["parameters"]
    
    # Initial investment (outflow)
    initial_investment = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["initial_investment"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add initial investment to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(initial_investment)
    
    # Handle updating events (business income and losses)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "business_income":
            # Get growth parameters from destination envelope
            _, theta_growth_dest = get_growth_parameters(envelopes, to_key=upd_params["to_key"])
            
            # Create recurring income function
            income_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": upd_params["end_time"]},
                f_in,
                P({"a": params["monthly_income"]}),
                theta_growth_dest
            )
            # Add to target envelope
            to_key = upd_params["to_key"]
            envelopes[to_key]["functions"].append(income_func)
            
        elif upd_type == "business_loss":
            # Create one-time loss function
            loss_func = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["loss_amount"]}),
                {"type": "None", "r": 0.0}
            )
            # Add to source envelope
            from_key = upd_params["from_key"]
            envelopes[from_key]["functions"].append(loss_func)

def retirement(event: dict, envelopes: dict):
    """Handle retirement withdrawals from retirement accounts."""
    params = event["parameters"]
    
    # Create recurring withdrawal function
    withdrawal_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_time"]},
        f_out,
        P({"b": params["amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add withdrawal function to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(withdrawal_func)
    
    # Create corresponding inflow to target envelope
    deposit_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["end_time"]},
        f_in,
        P({"a": params["amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add deposit function to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(deposit_func)

def buy_house(event: dict, envelopes: dict):
    """Handle house purchase with mortgage, appreciation, and property taxes."""
    params = event["parameters"]
    
    # Handle downpayment (outflow)
    downpayment_func = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["downpayment"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add downpayment to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(downpayment_func)
    
    # Create house value tracking function with appreciation
    house_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["home_value"]}),
        {"type": "Appreciation", "r": params["appreciation_rate"]}
    )
    
    # Add house value to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(house_func)
    
    # Create mortgage payments
    loan_amount = params["home_value"] - params["downpayment"]
    mortgage_func = R(
        {"t0": params["start_time"], "dt": 365/12, "tf": params["start_time"] + params["loan_term_years"]*365},
        f_mortgage,
        P({"P": loan_amount, "r": params["loan_rate"], "y": params["loan_term_years"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add mortgage payments to source envelope
    envelopes[from_key]["functions"].append(mortgage_func)
    
    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "new_appraisal":
            # Update house value with new appraisal
            new_house_func = T(
                {"t_k": upd_params["start_time"]},
                f_in,
                P({"a": upd_params["appraised_value"]}),
                {"type": "Appreciation", "r": params["appreciation_rate"]}
            )
            envelopes[to_key]["functions"].append(new_house_func)
            
        elif upd_type == "extra_mortgage_payment":
            # Handle extra payment
            extra_payment = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(extra_payment)
            
        elif upd_type == "late_payment":
            # Handle late payment
            late_payment = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(late_payment)
            
        elif upd_type == "sell_house":
            # Handle house sale
            sale_value = T(
                {"t_k": upd_params["start_time"]},
                f_in,
                P({"a": upd_params["sale_price"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["to_key"]]["functions"].append(sale_value)
            
            # Remove house value from tracking
            house_removal = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": params["home_value"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(house_removal)

def buy_home_insurance(event: dict, envelopes: dict):
    """Handle home insurance purchase and related damage events."""
    params = event["parameters"]
    
    # Create monthly premium payment function
    premium_func = R(
        {"t0": params["start_time"], "dt": 30, "tf": float('inf')},
        f_out,
        P({"b": params["monthly_premium"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add premium payments to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(premium_func)
    
    # Handle updating events (damage events)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type in ["tornado_damage", "house_fire", "flood_damage"]:
            # Calculate insurance payout
            damage_cost = upd_params["damage_cost"]
            coverage = upd_params.get("insurance_coverage", params["coverage_percentage"])
            payout = damage_cost * coverage
            
            # Handle deductible (outflow)
            deductible = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": params["deductible"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[from_key]["functions"].append(deductible)
            
            # Handle insurance payout (inflow)
            if payout > 0:
                payout_func = T(
                    {"t_k": upd_params["start_time"]},
                    f_in,
                    P({"a": payout}),
                    {"type": "None", "r": 0.0}
                )
                to_key = upd_params.get("to_key", from_key)
                envelopes[to_key]["functions"].append(payout_func)

def buy_car(event: dict, envelopes: dict):
    """Handle car purchase with loan and related events."""
    params = event["parameters"]
    
    # Handle downpayment (outflow)
    downpayment_func = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["downpayment"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add downpayment to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(downpayment_func)
    
    # Create car value tracking function with depreciation
    car_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["car_value"]}),
        {"type": "Depreciation", "r": 0.15}
    )
    
    # Add car value to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(car_func)
    
    # Create car loan payments
    loan_amount = params["car_value"] - params["downpayment"]
    loan_func = R(
        {"t0": params["start_time"], "dt": 365/12, "tf": params["start_time"] + params["loan_term_years"]*365},
        f_mortgage,
        P({"P": loan_amount, "r": params["loan_rate"], "y": params["loan_term_years"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add loan payments to source envelope
    envelopes[from_key]["functions"].append(loan_func)
    
    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "pay_loan_early":
            # Handle early loan payment
            early_payment = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(early_payment)
            
        elif upd_type == "car_repair":
            # Handle repair cost
            repair_cost = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["cost"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(repair_cost)

def have_kid(event: dict, envelopes: dict):
    """Handle child-related events and expenses."""
    params = event["parameters"]
    
    # Handle initial costs (outflow)
    initial_costs = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["initial_costs"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add initial costs to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(initial_costs)
    
    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "childcare_costs":
            # Create recurring childcare cost function
            childcare_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": upd_params["start_time"] + upd_params["end_days"]},
                f_out,
                P({"b": upd_params["monthly_cost"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(childcare_func)
            
        elif upd_type == "college_fund":
            # Handle initial college fund contribution
            initial_contribution = T(
                {"t_k": upd_params["start_time"]},
                f_out,
                P({"b": upd_params["initial_contribution"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(initial_contribution)
            
            # Create recurring college fund contribution function
            contribution_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": upd_params["start_time"] + upd_params["end_days"]},
                f_out,
                P({"b": upd_params["monthly_contribution"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(contribution_func)
            
            # Create corresponding inflow to college fund envelope
            _, theta_growth_college = get_growth_parameters(envelopes, to_key=upd_params["to_key"])
            fund_inflow = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": upd_params["start_time"] + upd_params["end_days"]},
                f_in,
                P({"a": upd_params["monthly_contribution"]}),
                theta_growth_college
            )
            envelopes[upd_params["to_key"]]["functions"].append(fund_inflow)

def marriage(event: dict, envelopes: dict):
    """Handle marriage-related expenses."""
    params = event["parameters"]
    
    # Create wedding cost function (outflow)
    wedding_cost = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["cost"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add wedding cost to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(wedding_cost)

def divorce(event: dict, envelopes: dict):
    """Handle divorce-related expenses and settlements."""
    params = event["parameters"]
    
    # Handle settlement payment (outflow)
    settlement = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["settlement_amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Handle attorney fees (outflow)
    attorney_fees = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["attorney_fees"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add both costs to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(settlement)
    envelopes[from_key]["functions"].append(attorney_fees)

def pass_away(event: dict, envelopes: dict):
    """Handle death by setting all envelope values to 0 after the event."""
    params = event["parameters"]
    death_time = params["start_time"]
    
    # For each envelope, create a function that returns 0 after death
    for envelope_name, envelope_data in envelopes.items():
        if "functions" in envelope_data:
            # For each function in the envelope, wrap it with D to return 0 after death
            new_funcs = []
            for func in envelope_data["functions"]:
                # Create a function that returns 0 for all time
                zero_func = lambda t: 0
                # Wrap the original function to return 0 after death
                new_func = lambda t, f=func, d=death_time: f(t) if t < d else 0
                new_funcs.append(new_func)
            
            # Replace the envelope's functions with the new ones
            envelopes[envelope_name]["functions"] = new_funcs

def buy_health_insurance(event: dict, envelopes: dict):
    """Handle health insurance purchase and medical expenses."""
    params = event["parameters"]
    
    # Create monthly premium payment function
    premium_func = R(
        {"t0": params["start_time"], "dt": 30, "tf": float('inf')},
        f_out,
        P({"b": params["monthly_premium"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add premium payments to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(premium_func)
    
    # Handle updating events (medical expenses)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "medical_expense":
            # Calculate out-of-pocket cost
            total_cost = upd_params["total_cost"]
            deductible = upd_params.get("deductible", params["deductible"])
            coverage = upd_params.get("insurance_coverage", params["coverage_percentage"])
            
            # Handle deductible (outflow)
            if deductible > 0:
                deductible_func = T(
                    {"t_k": upd_params["start_time"]},
                    f_out,
                    P({"b": deductible}),
                    {"type": "None", "r": 0.0}
                )
                envelopes[upd_params["from_key"]]["functions"].append(deductible_func)
            
            # Handle remaining out-of-pocket cost
            remaining_cost = total_cost - deductible
            out_of_pocket = remaining_cost * (1 - coverage)
            if out_of_pocket > 0:
                out_of_pocket_func = T(
                    {"t_k": upd_params["start_time"]},
                    f_out,
                    P({"b": out_of_pocket}),
                    {"type": "None", "r": 0.0}
                )
                envelopes[upd_params["from_key"]]["functions"].append(out_of_pocket_func)

def buy_life_insurance(event: dict, envelopes: dict):
    """Handle life insurance purchase and coverage changes."""
    params = event["parameters"]
    
    # Create monthly premium payment function
    premium_func = R(
        {"t0": params["start_time"], "dt": 30, "tf": params["start_time"] + params["term_years"] * 365},
        f_out,
        P({"b": params["monthly_premium"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add premium payments to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(premium_func)
    
    # Handle updating events (coverage changes)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "increase_coverage":
            # Create new premium payment function with updated amount
            new_premium_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": params["start_time"] + params["term_years"] * 365},
                f_out,
                P({"b": params["new_monthly_premium"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[from_key]["functions"].append(new_premium_func)

def receive_government_aid(event: dict, envelopes: dict):
    """Handle regular government benefit payments."""
    params = event["parameters"]
    
    # Create recurring payment function
    aid_func = R(
        {"t0": params["start_time"], "dt": params["frequency_days"], "tf": params["start_time"] + params["end_days"]},
        f_in,
        P({"a": params["amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add aid payments to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(aid_func)

def invest_money(event: dict, envelopes: dict):
    """Handle investment of money and related events."""
    params = event["parameters"]
    
    # Handle initial investment (outflow)
    initial_investment = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add initial investment to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(initial_investment)
    
    # Get growth parameters from destination envelope
    _, theta_growth_dest = get_growth_parameters(envelopes, to_key=params["to_key"])
    
    # Create investment growth function
    investment_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["amount"]}),
        theta_growth_dest
    )
    
    # Add investment growth to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(investment_func)
    
    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "Reoccuring Dividend Payout":
            # Handle dividend payments
            dividend_func = T(
                {"t_k": upd_params["start_time"]},
                f_in,
                P({"a": params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["to_key"]]["functions"].append(dividend_func)
            
        elif upd_type == "Reoccuring Contribution":
            # Handle recurring contributions
            contribution_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": upd_params["end_time"]},
                f_out,
                P({"b": params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["from_key"]]["functions"].append(contribution_func)
            
            # Add corresponding investment growth
            new_investment_func = T(
                {"t_k": upd_params["start_time"]},
                f_in,
                P({"a": upd_params["amount"]}),
                theta_growth_dest
            )
            envelopes[to_key]["functions"].append(new_investment_func)

def high_yield_savings_account(event: dict, envelopes: dict):
    """Handle high-yield savings account with daily interest."""
    params = event["parameters"]
    
    # Handle initial deposit (outflow)
    initial_deposit = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add initial deposit to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(initial_deposit)
    
    # Get growth parameters from destination envelope
    _, theta_growth_dest = get_growth_parameters(envelopes, to_key=params["to_key"])
    
    # Create savings growth function with daily compounding
    savings_func = T(
        {"t_k": params["start_time"]},
        f_in,
        P({"a": params["amount"]}),
        theta_growth_dest
    )
    
    # Add savings growth to target envelope
    to_key = params["to_key"]
    envelopes[to_key]["functions"].append(savings_func)

def pay_taxes(event: dict, envelopes: dict):
    """Handle tax payments and refunds."""
    params = event["parameters"]
    
    # Handle tax payment (outflow)
    tax_payment = T(
        {"t_k": params["start_time"]},
        f_out,
        P({"b": params["total_tax_due"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add tax payment to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(tax_payment)
    
    # Handle updating events (tax refunds)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "receive_tax_refund":
            # Handle tax refund (inflow)
            refund_func = T(
                {"t_k": upd_params["start_time"]},
                f_in,
                P({"a": params["amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[upd_params["to_key"]]["functions"].append(refund_func)

def buy_groceries(event: dict, envelopes: dict):
    """Handle recurring grocery expenses."""
    params = event["parameters"]
    
    # Create recurring monthly grocery payment function
    grocery_func = R(
        {"t0": params["start_time"], "dt": 30, "tf": params["start_time"] + params["end_days"]},
        f_out,
        P({"b": params["monthly_amount"]}),
        {"type": "None", "r": 0.0}
    )
    
    # Add grocery payments to source envelope
    from_key = params["from_key"]
    envelopes[from_key]["functions"].append(grocery_func)
    
    # Handle updating events (amount changes)
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        
        if upd_type == "update_amount":
            # Create new payment function with updated amount
            new_grocery_func = R(
                {"t0": upd_params["start_time"], "dt": 30, "tf": params["start_time"] + params["end_days"]},
                f_out,
                P({"b": params["new_amount"]}),
                {"type": "None", "r": 0.0}
            )
            envelopes[from_key]["functions"].append(new_grocery_func)
