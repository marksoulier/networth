from typing import Callable, Dict, Any
import numpy as np

#######################################################################################################################################
# Base Utilities
#######################################################################################################################################

def u(t: float) -> float:
    return 1.0 if t >= 0 else 0.0

def T(tk: float, f: Callable[[Callable[[float], Dict[str, float]], float], Callable[[float], float]], theta: Callable[[float], Dict[str, float]] = None) -> Callable[[float], float]:
    if theta is None:
        theta = P({})
    return lambda t: f(theta, tk)(t - tk) * u(t - tk)

def R(
    t0: float, dt: float, tf: float, f: Callable[[Callable[[float], Dict[str, float]], float], Callable[[float], float]],
    theta: Callable[[float], Dict[str, float]],
    overrides: Dict[int, Callable[[float], Dict[str, float]]] = {}
) -> Callable[[float], float]:
    return lambda t: sum(
        (f(overrides[i] if i in overrides else theta, ti))(t - ti) * u(t - ti)
        for i in range(int((tf - t0) // dt) + 1)
        if (ti := t0 + i * dt) <= tf
    )

def D(t_delta: float, f_before: Callable[[float], float], f_after: Callable[[float], float]) -> Callable[[float], float]:
    return lambda t: f_before(t) if t < t_delta else f_after(t)

def gamma(theta: Callable[[float], Dict[str, float]], theta_change: Dict[str, float], t_star: float) -> Callable[[float], Dict[str, float]]:
    def theta_t(t: float) -> Dict[str, float]:
        if t < t_star:
            return theta(t)
        else:
            return {**theta(t), **theta_change}
    return theta_t

def P(params: Dict[str, Any]) -> Callable[[float], Dict[str, Any]]:
    """Convert a dictionary of parameters into a time-varying parameter function.
    The returned function will always return the same parameters regardless of time."""
    return lambda t: params

#######################################################################################################################################
# Base Functions
#######################################################################################################################################


# --- Function Definitions with θ parameter docs ---


# θ_in = {"a": inflow_amount}
def f_in(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["a"] * u(t)

# θ_out = {"b": outflow_amount}
def f_out(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: -params["b"] * u(t)

# θ = {"P": principal, "r": daily_rate}
def f_com(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["P"] * (1 + params["r"] / 365) ** t * u(t)

# θ_sal = {"S": salary, "p": periods, "r_SS": ss_tax, "r_Med": med_tax, "r_Fed": fed_tax, "r_401k": match}
def f_sal(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: (params["S"] / params["p"]) * (1 - (params["r_SS"] + params["r_Med"] + params["r_Fed"] + params["r_401k"])) * u(t)

# θ_app = {"V0": initial_value, "r_app": annual_appreciation}
def f_app(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    return lambda t: theta(t_i)["V0"] * (1 + theta(t_i)["r_app"]) ** (t / 365)

# θ_dep = {"V0": initial_value, "r_dep": annual_depreciation}
def f_dep(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    return lambda t: theta(t_i)["V0"] * (1 - theta(t_i)["r_dep"]) ** (t / 365)


#######################################################################################################################################
# Financial Functions
#######################################################################################################################################

# Define remaining symbolic functions in Python based on the LaTeX document

from typing import Dict, Callable
import numpy as np

# --- Additional Financial Function Definitions ---

# θ_401 = {"S": salary, "p": periods, "r_401": rate, "r_growth": compounding_rate}
def f_401(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_com(P({"P": (params["S"] / params["p"]) * params["r_401"], "r": params["r_growth"]}), t_i)(t)

# θ_principal = {"P": loan_amount, "r": annual_rate, "y": years, "p_mortgage": fixed_monthly_payment}
def f_principal(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    def func(t: float) -> float:
        months = int(t / (365 / 12))
        r = params["r"]
        y = params["y"]
        Loan = params["P"]
        # Calculate default mortgage payment if not provided
        default_payment = Loan * (r / 12) * ((1 + r / 12) ** (12 * y)) / (((1 + r / 12) ** (12 * y)) - 1)
        p_m = params.get("p_mortgage", default_payment)
        payment = Loan * ((1 + r / 12) ** months) * (r / 12) / (((1 + r / 12) ** (12 * y)) - 1)
        mortgage_amt = f_mortgage(P({"P": Loan, "r": r, "y": y}), t_i)(t)
        return payment + max(mortgage_amt - p_m, 0)
    return func

# θ_house = {"H0": value, "r_app": appreciation, "t_buy": start_day, "y": years, "D": down_payment, "Omega": overrides}
# θ_principal = {"P": loan_amount, "r": rate, "y": years, "p_mortgage": fixed_payment}
def f_buy_house(theta_h: Callable[[float], Dict[str, float]], theta_p: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params_h = theta_h(t_i)  # Evaluate parameters at time of occurrence
    params_p = theta_p(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_app(P({"V0": params_h["H0"], "r_app": params_h["r_app"]}), t_i)(t) - (
        params_h["H0"] - params_h["D"] - R(params_h["t_buy"], 365 / 30, params_h["t_buy"] + params_h["y"] * 365, f_principal, theta_p)(t)
    )


# θ_car = {"C0": car_value, "r_dep": depreciation_rate, "t_buy": start_day, "y": years, "D": down_payment}
# θ_principal = {"P": loan_amount, "r": annual_rate, "y": years, "p_loan": fixed_monthly_payment}
def f_buy_car(theta_c: Callable[[float], Dict[str, float]], theta_p: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta_c(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_dep(P({"V0": params["C0"], "r_dep": params["r_dep"]}), t_i)(t) - (
        params["C0"] - params["D"] - R(
            params["t_buy"],
            365 / 12,
            params["t_buy"] + params["y"] * 365,
            f_principal,
            theta_p
        )(t)
    )

# θ_mortgage = {"P": principal, "r": annual_rate, "y": years}
def f_mortgage(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["P"] * (params["r"] / 12) * ((1 + params["r"] / 12) ** (12 * params["y"])) / (((1 + params["r"] / 12) ** (12 * params["y"])) - 1)

# θ_insurance = {"p0": base_premium, "r_adj": annual_rate}
def f_insurance(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["p0"] * (1 + params["r_adj"]) ** (t / 365)

# θ_maint = {"m0": base_cost, "alpha": slope, "t0": start_time}
def f_maint(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["m0"] + params["alpha"] * (t - params["t0"])

# θ_inf = {"r_inf": inflation_rate, "t_today": reference_day}
def f_inflation_adjust(W: Callable[[float], float], theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: W(t) / ((1 + params["r_inf"]) ** ((t - params["t_today"]) / 365)) if t >= params["t_today"] else W(t)

# θ_empirical = {"V_obs": observed_value, "t_k": observation_time}
def f_empirical(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: params["V_obs"] if np.isclose(t, params["t_k"]) else 0.0

###################################################################################
# Events and update functions
###################################################################################
from typing import Callable, Dict, Any, Union

# θ_purchase = {"m": amount}
def f_purchase(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_out(P({"b": params["m"]}), t_i)(t)

# θ_job = {"S": salary, "p": periods_per_year, "r_Fed": federal_tax, "r_SS": ss_tax, "r_Med": medicare, "r_401k": retirement_contrib, "time_start": When you start the job, "time_end": When you end the job}
def f_get_job(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: R(params['time_start'], 365 / params["p"], params['time_end'], f_sal, theta)(t)


# Return function theta(t) for raise
def raise_override(theta: Callable[[float], Dict[str, float]], new_salary: float, t_raise: float) -> Callable[[float], Dict[str, float]]:
    return gamma(theta, {"S": new_salary}, t_raise)

# θ_bonus = {"b": bonus_amount}
def f_get_bonus(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_in(P({"a": params["b"]}), t_i)(t)

# θ_startbiz = {"a": initial_expense}
def f_start_business(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_out(P({"b": params["a"]}), t_i)(t)

# θ_biz_in = {"t0": start_time, "Δt": interval, "tf": end_time, "m": amount}
def f_business_income(theta: Callable[[float], Dict[str, Union[float, int]]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: R(params["t0"], params["Δt"], params["tf"], f_in, P({"a": params["m"]}))(t)

# Return function theta(t) for business income update
def update_business_income(theta: Callable[[float], Dict[str, Any]], new_m: float, t_update: float) -> Callable[[float], Dict[str, Any]]:
    return gamma(theta, {"m": new_m}, t_update)

# θ_ret = {"t0": start_time, "Δt": interval, "tf": end_time, "w": withdrawal}
def f_retirement(theta: Callable[[float], Dict[str, Union[float, int]]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: R(params["t0"], params["Δt"], params["tf"], f_out, P({"b": params["w"]}))(t)

# θ_hysa = {"p": principal, "r_y": interest_rate}
def f_hysa(theta: Callable[[float], Dict[str, float]], t_i: float) -> Callable[[float], float]:
    params = theta(t_i)  # Evaluate parameters at time of occurrence
    return lambda t: f_com(P({"P": params["p"], "r": params["r_y"]}), t_i)(t)

# Return function theta(t) for 401k update
def update_401k(theta: Callable[[float], Dict[str, Any]], new_r_401k: float, t_update: float) -> Callable[[float], Dict[str, Any]]:
    return gamma(theta, {"r_401k": new_r_401k}, t_update)

# Return function theta(t) for depreciation adjustment
def adjust_depreciation(theta: Callable[[float], Dict[str, Any]], new_r_dep: float, t_update: float) -> Callable[[float], Dict[str, Any]]:
    return gamma(theta, {"r_dep": new_r_dep}, t_update)

# Return function theta(t) for mortgage update
def adjust_mortgage(theta: Callable[[float], Dict[str, Any]], new_payment: float, t_update: float) -> Callable[[float], Dict[str, Any]]:
    return gamma(theta, {"monthly_payment": new_payment}, t_update)








########################################################################################
# Premium Functions
#########################################################################################


# Monte Carlo placeholder
# θ_monte = {"mu": mean_return, "sigma": volatility, "dt": step_size}
def f_monte(theta: Callable[[float], Dict[str, float]], w: Callable[[float], float]) -> Callable[[float], float]:
    def func(t: float) -> float:
        mu, sigma, dt = theta(t)["mu"], theta(t)["sigma"], theta(t)["dt"]
        n = int(t // dt)
        Z = np.random.normal(0, 1, n)
        exponent = np.sum((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
        return w(t) * np.exp(exponent)
    return func






###########################################################3
#Examples

# Example 1: You receive $10 as a one-time gift on day 5 and spend $5 of it on day 10.
example1_envelopes = {
    "cash": [
        T(365, f_in, P({"a": 10})),
        T(2*365, f_out, P({"b": 5}))
    ]
}

# Example 2: You earn a $76,000/year salary with standard tax deductions and spend $10,000 every year on vacations.
example2_envelopes = {
    "cash": [
        R(0, 365/26, 40*365, f_sal, P({
            "S": 76000, "p": 26,
            "r_SS": 0.062, "r_Med": 0.0145,
            "r_Fed": 0.12, "r_401k": 0.06
        })),
        R(0, 365, 40*365, f_out, P({"b": 10000}))
    ]
}


# Example 3: You deposit $1000 into a high-yield savings account at 4.5% interest, then deposit an additional $200 on day 180.
example3_envelopes = {
    "cash": [
        T(0, f_com, P({"P": 1000, "r": 0.045})),
        T(180, f_com, P({"P": 200, "r": 0.045}))
    ]
}

# Example 4: You buy a $300k house with 20% down, 30-year mortgage at 4%, appreciating at 5% annually.
example4_envelopes = {
    "house": [
        f_buy_house(
            P({
                "H0": 300000,
                "r_app": 0.05,
                "t_buy": 0,
                "y": 30,
                "D": 60000,
                "Omega": []
            }),
            P({
                "P": 240000,
                "r": 0.04,
                "y": 30
            }),
            0
        )
    ],
    "cash": [
        R(0, 30.42, 30 * 365, f_mortgage, P({"P": -240000, "r": 0.04, "y": 30}))
    ]
}

# Example 5: You contribute $500 monthly to a 401(k) with 7% growth, and at year 5, the value is corrected to $40,000.
example5_envelopes = {
    "retirement_401k": [
        D(
            4*365,  # Year 5 correction point
            R(0, 30.42, 1825, f_com, P({"P": 500, "r": 0.07})),
            lambda t: R(4*365, 30.42, 60 * 365, f_com, P({"P": 500, "r": 0.07}))(t) +
                      T(4*365, f_in, P({"a": 40000}))(t)
        )
    ]
}

# Example 6: Weekly salary of $70k with raises to $80k at year 3 and $90k at year 5, including standard deductions. Start job at day 50 and go till year 10.
example6_envelopes = {
    "cash": [
        f_get_job(
            raise_override(
                raise_override(
                    P({
                        "S": 10000, "p": 52,
                        "r_Fed": 0.12, "r_SS": 0.062,
                        "r_Med": 0.0145, "r_401k": 0.06,
                        'time_start': 50, 'time_end': 365*12
                    }),
                    new_salary=50000, t_raise=3 * 365
                ),
                new_salary=1000, t_raise=5 * 365
            ),
            50
        )
    ]
}

from events_library.base_functions import evaluate_results, show_visual


# t_end = 20*365
# interval = 5
# t_range = np.arange(0, t_end, interval)

# test_list = [example1_envelopes, example2_envelopes, example3_envelopes, example4_envelopes, example5_envelopes, example6_envelopes]

# for example in test_list:
#     results = evaluate_results(example, 0, t_end, interval)
#     show_visual(results, t_range)









######################################################################################################################
# Events
######################################################################################################################
def get_job(event: dict, envelopes: dict):
    params = event["parameters"]

    # Base job parameters dictionary for P(...)
    theta_base = {
        "S": params["salary"],
        "p": params["pay_period"],
        "r_Fed": params["federal_income_tax"],
        "r_SS": params["social_security_tax"],
        "r_Med": params["medicare_tax"],
        "r_401k": params["401k_contribution"],
        "r_state": params["state_income_tax"],
        "time_start": params["start_time"],
        "time_end": params["end_time"],
    }

    # Compose the base theta(t)
    theta = P(theta_base)

    # Handle updating events
    for upd in event.get("updating_events", []):
        upd_type = upd["type"]
        upd_params = upd.get("parameters", {})
        print(upd_params)
        
        if upd_type == "get_a_raise":
            theta = raise_override(theta, upd_params["salary"], upd_params["start_time"])

        elif upd_type == "change_401k_contribution":
            theta = update_401k(theta, upd_params["401k_contribution"], upd_params["start_time"])

        elif upd_type == "get_a_bonus":
            envelopes["Cash"].append(
                T(upd_params["start_time"], f_in, P({"a": upd_params["bonus"]}))
            )

        # Add more `elif` cases as needed

    # Final wrapped job function
    to_key = params["to_key"]
    envelopes[to_key].append(f_get_job(theta, params["start_time"]))

