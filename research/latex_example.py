from investment_test import *

# Define time range (in years)
t_range = np.arange(0, 1, 1/365)  # time from 0 to 105 years

# Create envelopes dictionary
envelopes = {
    'W1': []  # cash envelope
}

# Convert days to years for the recurring payments
salary_interval = 30/365  # 30 days converted to years
rent_interval = 30/365    # 30 days converted to years
rent_start = 5/365       # 5 days converted to years

# Add salary and rent to W1 envelope
envelopes['W1'].append(lambda t: recurring_inflow(3000, 0, 105, t, interval=salary_interval))  # Salary every 30 days
envelopes['W1'].append(lambda t: recurring_outflow(1000, rent_start, 105, t, interval=rent_interval))  # Rent every 30 days

# Evaluate envelope over time
results = {}
for key in envelopes:
    results[key] = np.zeros_like(t_range)
    for func in envelopes[key]:
        results[key] += np.array([func(t) for t in t_range])

# Plot results
plt.figure(figsize=(12, 6))
plt.plot(t_range, results['W1'], label='Cash (W1)')
plt.title('Cash Flow with Salary and Rent Payments')
plt.xlabel('Time (years)')
plt.ylabel('Value ($)')
plt.legend()
plt.grid(True)
plt.show()






