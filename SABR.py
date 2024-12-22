import numpy as np
from scipy.stats import norm

# SABR model parameters
F = 100     # Forward price
K = 90      # Strike price
T = 1       # Time to maturity in years
alpha = 0.25
beta = 1     # Lognormal model
nu = 0.4
rho = -0.3
dt = 1/252   # Time step (daily)

# Simulate the SABR process using Euler-Maruyama
np.random.seed(42)  # For reproducibility
n_steps = int(T / dt)  # Number of time steps

# Initialize forward price and volatility
F_t = F
sigma_t = alpha
F_paths = []
sigma_paths = []

# Simulate paths for F and sigma
for _ in range(n_steps):
    dW1 = np.random.normal(0, np.sqrt(dt))
    dW2 = np.random.normal(0, np.sqrt(dt))
    
    # Update forward price and volatility using Euler-Maruyama
    F_t += sigma_t * F_t**beta * np.sqrt(dt) * dW1
    sigma_t += nu * sigma_t * np.sqrt(dt) * dW2
    
    # Store the paths
    F_paths.append(F_t)
    sigma_paths.append(sigma_t)

# Final values at maturity
F_final = F_paths[-1]
sigma_final = sigma_paths[-1]

# Calculate the option price (European call)
call_price = max(F_final - K, 0)

# Black-Scholes formula to find implied volatility
def black_scholes_call(F, K, T, sigma):
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return F * norm.cdf(d1) - K * norm.cdf(d2)

# Find implied volatility by solving Black-Scholes equation
def implied_volatility(F, K, T, market_price):
    # Use a numerical solver to find the implied volatility
    from scipy.optimize import fmin
    objective = lambda sigma: np.abs(black_scholes_call(F, K, T, sigma) - market_price)
    return fmin(objective, 0.2)[0]

# Find implied volatility from the simulated call price
implied_vol = implied_volatility(F_final, K, T, call_price)

print(f"Simulated Call Option Price: {call_price}")
print(f"Implied Volatility: {implied_vol}")
