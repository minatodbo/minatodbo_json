import numpy as np
import scipy.stats as si
from scipy.optimize import newton

# Black-Scholes Formula for option pricing
def black_scholes(S, K, T, r, sigma, option_type):
    """
    Calculate the Black-Scholes price of a European option.
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'C':
        return S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
    elif option_type == 'P':
        return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
    else:
        raise ValueError("Invalid option type. Use 'C' for call or 'P' for put.")

# Vega: Sensitivity of option price to volatility (dPrice/dVolatility)
def vega(S, K, T, r, sigma):
    """
    Calculate Vega (sensitivity to volatility) for Black-Scholes.
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * si.norm.pdf(d1) * np.sqrt(T)

# Implied Volatility Function
def implied_volatility(S, K, T, r, market_price, option_type):
    """
    Calculate the implied volatility using Newton's method.
    """
    # Initial guess: 20% volatility
    sigma_guess = 0.2

    # Define the function to minimize: f(sigma) = BS_price - market_price
    def price_difference(sigma):
        return black_scholes(S, K, T, r, sigma, option_type) - market_price

    try:
        # Use Newton's method for fast root-finding
        iv = newton(price_difference, sigma_guess, fprime=lambda sigma: vega(S, K, T, r, sigma), tol=1e-8, maxiter=100)
        return iv
    except RuntimeError:
        # If Newton's method fails, return NaN
        return np.nan

# Example Test
S = 6000  # Spot price
K = 5000  # Strike price
T = 0.09  # Time to expiration (in years)
r = 0.04  # Risk-free rate
market_price = 970  # Market price of the option
option_type = 'C'  # 'C' for call, 'P' for put

iv = implied_volatility(S, K, T, r, market_price, option_type)
if np.isnan(iv):
    print("Failed to compute implied volatility.")
else:
    print(f"Implied Volatility: {iv:.4%}")
