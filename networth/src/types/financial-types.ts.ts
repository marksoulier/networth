// Types for financial simulation

// Parameter types
export type ParameterType = 'time' | 'money' | 'rate' | 'interval' | 'end_time';

// Function types
export type FunctionType =
  | 'inflow'
  | 'outflow'
  | 'compound_invest_inflow'
  | 'compound_invest_outflow'
  | 'recurring_inflow'
  | 'recurring_outflow'
  | '';

// Event types
export type EventType = 'purchase' | 'pay_check' | 'compound_investment' | 'having_a_baby' | 'getting_a_job' | 'ending_a_job' | 'groceries';

// Parameter inside a function
export interface FunctionParameter {
  id: number; // unique identifier for the parameter
  type: ParameterType; // the parameter type or category
  value: number; // the value of the parameter
}

// Function definitions (inflow/outflow)
export interface FinancialFunction {
  id: number; // unique identifier for the function
  type: FunctionType; // the function type or category
  parameters: FunctionParameter[]; // the parameters of the function, should be set for a specific type of function, should have a time parameter.
}

// Event parameter (reference to a function parameter)
export interface EventParameter {
  id: number;
  type: 'time' | 'money' | 'amount' | 'rate' | 'expected_return' | 'from_key' | 'to_key';
  value: number | string;
}

// Events (income/spending)
export interface FinancialEvent {
  id: number;
  type: string;
  description: string;
  parameters: EventParameter[];
}

// Envelope (container for functions)
export interface Envelope {
  id: number; // unique identifier for the envelope
  name: string; // the name of the envelope
  function_ids: number[]; // the ids of the functions that are in the envelope
}

// Complete financial data structure
export interface FinancialProblem {
  envelopes: Envelope[];
  functions: FinancialFunction[];
  events: FinancialEvent[];
}
