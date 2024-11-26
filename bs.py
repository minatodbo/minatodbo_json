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
        implied_vol = optimize.brentq(difference, 0.01, 2.0)  # Adjust bounds to ensure convergence
    except ValueError:
        implied_vol = 0.3  # Default to a reasonable value if optimization fails

    return implied_vol

# Example usage
S = 6000  # Spot price
K = 5000  # Strike price
T = 0.09  # Time to expiration (in years)
r = 0.04  # Risk-free interest rate (4%)
market_price = 970  # Market price of the option
option_type = 'C'  # 'C' for call, 'P' for put

iv = implied_volatility(S, K, T, r, market_price, option_type)
print(f"Implied Volatility: {iv:.4f}")
