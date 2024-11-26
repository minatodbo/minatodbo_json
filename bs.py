import numpy as np
import scipy.stats as si
from scipy import optimize

# Black-Scholes Formula for option pricing
def black_scholes(S, K, T, r, sigma, option_type):
    """
    Calculate the Black-Scholes price of a European option.
    S: Spot price of the asset
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free interest rate
    sigma: Volatility of the asset
    option_type: 'C' for call, 'P' for put
    """
    # Compute d1 and d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'C':
        option_price = S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
    elif option_type == 'P':
        option_price = K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
    else:
        raise ValueError("Option type must be 'C' (call) or 'P' (put)")
    
    return option_price

# Function to calculate implied volatility using Brent's method
def implied_volatility(S, K, T, r, market_price, option_type):
    """
    Calculate the implied volatility for a European option using Brent's method.
    S: Spot price of the asset
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free interest rate
    market_price: Market price of the option
    option_type: 'C' for call, 'P' for put
    """
    # Define the function to calculate the difference between market price and Black-Scholes price
    def difference(sigma):
        return black_scholes(S, K, T, r, sigma, option_type) - market_price

    # Use Brent's method to solve for the implied volatility
    try:
        # Use reasonable bounds for volatility. For example, implied volatility is generally between 0.01 and 5.
        implied_vol = optimize.brentq(difference, 0.01, 5.0)  # No hardcoding of 0.3, range from 0.01 to 5
    except ValueError:
        # If optimization fails (it could happen in extreme edge cases), return a large value or error
        implied_vol = np.nan
    
    return implied_vol

# Example usage
S = 6000  # Spot price
K = 5000  # Strike price
T = 0.09  # Time to expiration (in years)
r = 0.04  # Risk-free interest rate (4%)
market_price = 970  # Market price of the option
option_type = 'C'  # 'C' for call, 'P' for put

iv = implied_volatility(S, K, T, r, market_price, option_type)
if np.isnan(iv):
    print("Failed to compute implied volatility.")
else:
    print(f"Implied Volatility: {iv:.4f}")
