import { useEffect } from 'react';
import { useFinancialProblem, loadFinancialProblemFromFile } from '../hooks/useFinancialProblem';

export const TestFinancialData = () => {
  const { financialProblem, setFinancialProblem } = useFinancialProblem();

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await loadFinancialProblemFromFile('/src/assets/financialproblem.json');
        console.log('Loaded Financial Problem:', data);
        setFinancialProblem(data);
      } catch (error) {
        console.error('Error loading financial data:', error);
      }
    };

    loadData();
  }, [setFinancialProblem]);

  // Log whenever financialData changes
  useEffect(() => {
    console.log('Current Financial Problem:', financialProblem);
  }, [financialProblem]);

  return (
    <div>
      <h2>Financial Data Test Component</h2>
      <p>Check the console to see the loaded financial data</p>
    </div>
  );
}; 