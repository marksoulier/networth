import { useState, useEffect, useCallback } from 'react';
import type { FinancialProblem, EventParameter, FinancialEvent } from '../types/financial-types.ts.ts';

/**
 * Custom hook to load and manage financial data
 * @param initialData Optional initial data to load
 * @returns The financial data state and mutation functions
 */
export const useFinancialProblem = (initialData?: FinancialProblem | string) => {
  // Initialize with empty state
  const [financialProblem, setFinancialProblem] = useState<FinancialProblem>({
    events: []
  });

  // Effect to load the initial data
  useEffect(() => {
    if (initialData) {
      try {
        // Parse the JSON if it's a string
        const parsedData = typeof initialData === 'string'
          ? JSON.parse(initialData)
          : initialData;

        // Type checking and validation
        if (!Array.isArray(parsedData.events)) {
          console.error('Invalid financial data: events must be an array');
          return;
        }

        // Validate events have required parameters
        const hasValidEvents = parsedData.events.every((event: FinancialEvent) => {
          const hasTime = event.parameters.some((param: EventParameter) => param.type === 'time');
          const hasAmount = event.parameters.some((param: EventParameter) =>
            ['money', 'amount'].includes(param.type)
          );
          return hasTime && hasAmount;
        });

        if (!hasValidEvents) {
          console.error('Invalid financial data: all events must have time and amount parameters');
          return;
        }

        // Set the validated data
        setFinancialProblem(parsedData);
      } catch (error) {
        console.error('Error parsing financial data:', error);
      }
    }
  }, [initialData]);

  // Mutation functions
  const updateEventTime = useCallback((eventId: number, newTime: number) => {
    setFinancialProblem(prev => {
      const updatedEvents = prev.events.map(event => {
        if (event.id === eventId) {
          // Update all time parameters in the event
          const updatedParameters = event.parameters.map(param => {
            if (param.type === 'time') {
              return { ...param, value: newTime };
            }
            return param;
          });
          return { ...event, parameters: updatedParameters };
        }
        return event;
      });

      return {
        ...prev,
        events: updatedEvents
      };
    });
  }, []);

  const updateEventAmount = useCallback((eventId: number, newAmount: number) => {
    setFinancialProblem(prev => {
      const updatedEvents = prev.events.map(event => {
        if (event.id === eventId) {
          // Update all money/amount parameters in the event
          const updatedParameters = event.parameters.map(param => {
            if (['money', 'amount'].includes(param.type)) {
              return { ...param, value: newAmount };
            }
            return param;
          });
          return { ...event, parameters: updatedParameters };
        }
        return event;
      });

      return {
        ...prev,
        events: updatedEvents
      };
    });
  }, []);

  const updateEventRate = useCallback((eventId: number, newRate: number) => {
    setFinancialProblem(prev => {
      const updatedEvents = prev.events.map(event => {
        if (event.id === eventId) {
          // Update all rate parameters in the event
          const updatedParameters = event.parameters.map(param => {
            if (param.type === 'rate' || param.type === 'expected_return') {
              return { ...param, value: newRate };
            }
            return param;
          });
          return { ...event, parameters: updatedParameters };
        }
        return event;
      });

      return {
        ...prev,
        events: updatedEvents
      };
    });
  }, []);

  return {
    financialProblem,
    setFinancialProblem,
    updateEventTime,
    updateEventAmount,
    updateEventRate
  };
};

/**
 * Utility function to load financial data from a JSON file
 * @param filePath Path to the JSON file
 * @returns Promise that resolves to the parsed financial data
 */
export const loadFinancialProblemFromFile = async (filePath: string): Promise<FinancialProblem> => {
  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      throw new Error(`Failed to load financial data: ${response.statusText}`);
    }

    const data = await response.json();
    return data as FinancialProblem;
  } catch (error) {
    console.error('Error loading financial data from file:', error);
    // Return empty data structure on error
    return {
      events: []
    };
  }
};