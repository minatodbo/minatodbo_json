import numpy as np
import scipy.stats as si
from scipy.optimize import brentq

# Black-Scholes formula to calculate the theoretical option price
def black_scholes(S, K, T, r, sigma, option_type):
    """
    Calculate the Black-Scholes option price for a given volatility.
    Args:
        S: Spot price of the underlying asset
        K: Strike price of the option
        T: Time to expiration (in years)
        r: Risk-free rate (annualized)
        sigma: Implied volatility
        option_type: 'C' for call, 'P' for put
    Returns:
        The theoretical option price according to the Black-Scholes model
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'C':
        return S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)  # Call option price
    elif option_type == 'P':
        return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)  # Put option price
    else:
        raise ValueError("Invalid option type. Use 'C' for Call or 'P' for Put.")

# Implied volatility function using Brent's method
def implied_volatility(S, K, T, r, market_price, option_type):
    """
    Calculate the implied volatility using Brent's method to solve for the price of the option.
    Args:
        S: Spot price of the underlying asset
        K: Strike price of the option
        T: Time to expiration (in years)
        r: Risk-free rate (annualized)
        market_price: Market price of the option
        option_type: 'C' for call, 'P' for put
    Returns:
        The implied volatility
    """
    def price_difference(sigma):
        """
        The difference between the Black-Scholes price and the market price.
        The root of this function gives us the implied volatility.
        """
        return black_scholes(S, K, T, r, sigma, option_type) - market_price

    # Set the lower and upper bounds for volatility
    low = 0.01  # Lower bound for volatility (1%)
    high = 2.0   # Upper bound for volatility (200%)
    
    # Handle case when the market price is too low for the Black-Scholes model to generate a proper IV
    if market_price <= 0:
        raise ValueError("Market price should be greater than zero.")
    
    theoretical_price = black_scholes(S, K, T, r, 0.2, option_type)  # Use an assumed volatility for price calculation
    
    # If the market price is much lower than the theoretical price, adjust the bounds to handle deep OTM or ITM
    if market_price < theoretical_price * 0.1:  # Deep OTM case
        low = 0.05  # Increase the lower bound to prevent too low volatility
        high = 1.5  # Decrease upper bound for deep OTM
    elif market_price > theoretical_price * 10:  # Deep ITM case (e.g., huge market price)
        low = 0.2  # Increase lower bound to prevent too low volatility
        high = 3.0  # Allow higher volatility for deep ITM options

    try:
        # Use Brent's method to find the root of price_difference
        implied_vol = brentq(price_difference, low, high, xtol=1e-8)
        return implied_vol
    except ValueError:
        raise RuntimeError("Failed to compute implied volatility: Check the inputs.")

# Example test case
S = 6000        # Spot price
K = 5000        # Strike price
T = 0.09        # Time to expiration (9%)
r = 0.04        # Risk-free rate (4%)
market_price = 970  # Market price of the option
option_type = 'C'   # Call option

# Compute the implied volatility
try:
    iv = implied_volatility(S, K, T, r, market_price, option_type)
    print(f"Implied Volatility: {iv:.4%}")
except RuntimeError as e:
    print(e)
