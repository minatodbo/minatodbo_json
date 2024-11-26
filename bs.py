import numpy as np
import scipy.stats as si
from scipy.optimize import brentq

# Black-Scholes Formula
def black_scholes(S, K, T, r, sigma, option_type):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'C':
        return S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
    elif option_type == 'P':
        return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
    else:
        raise ValueError("Option type must be 'C' (call) or 'P' (put).")

# Implied Volatility
def implied_volatility(S, K, T, r, market_price, option_type):
    def price_difference(sigma):
        return black_scholes(S, K, T, r, sigma, option_type) - market_price

    try:
        # Wider bounds for implied volatility search
        iv = brentq(price_difference, 0.001, 10.0, xtol=1e-8)
        return iv
    except ValueError:
        # Return NaN if the solver fails
        return np.nan

# Test Input
S = 6000         # Spot price
K = 5000         # Strike price
T = 0.09         # Time to expiration (years)
r = 0.04         # Risk-free rate
market_price = 970  # Market price of the option
option_type = 'C'   # Call option

# Calculate Implied Volatility
iv = implied_volatility(S, K, T, r, market_price, option_type)
if np.isnan(iv):
    print("Failed to compute implied volatility.")
else:
    print(f"Implied Volatility: {iv:.4%}")
