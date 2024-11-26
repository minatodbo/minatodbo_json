import numpy as np
import scipy.stats as si
from scipy import optimize

def calcimpliedvol_(S, K, T, r, marketoptionPrice, option_type):
    # Handle edge cases for zero prices or strikes
    if S == 0 or K == 0:
        return 0
    if T == 0:
        T = 1  # Assume T = 1 year if T is 0
    
    # Check if the option is deep ITM
    if option_type == "C":  # Call option
        intrinsic_value = max(S - K, 0)
    elif option_type == "P":  # Put option
        intrinsic_value = max(K - S, 0)
    
    # Define a threshold for "deep ITM" based on the difference between market price and intrinsic value
    deep_ITM_threshold = 0.05  # 5% difference between intrinsic value and market price
    if abs(marketoptionPrice - intrinsic_value) < deep_ITM_threshold:
        # For deep ITM, allow high implied volatility but avoid failure in the solver
        # Here we use a broader range for implied volatility search
        min_volatility = 0.01  # Reasonable lower bound for volatility
        max_volatility = 200  # Reasonable upper bound for deep ITM cases
    else:
        # For regular options, we set the volatility bounds more conservatively
        min_volatility = 0.001
        max_volatility = 5  # Volatility typically doesn't go above 5 for most options
    
    try:
        # Black-Scholes formula for option price
        def bs_price(sigma):
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - (sigma * np.sqrt(T))
            
            if option_type == "C":  # Call option
                BSprice_call = S * si.norm.cdf(d1, 0, 1) - K * np.exp(-r * T) * si.norm.cdf(d2, 0, 1)
                fx = BSprice_call - marketoptionPrice
            elif option_type == "P":  # Put option
                BSprice_put = K * np.exp(-r * T) * si.norm.cdf(-d2, 0, 1) - S * si.norm.cdf(-d1, 0, 1)
                fx = BSprice_put - marketoptionPrice
            else:
                raise ValueError("Option type must be 'C' or 'P'.")
            
            return fx
        
        # Use the brentq method to find implied volatility with adjusted bounds
        implied_vol = optimize.brentq(bs_price, min_volatility, max_volatility, maxiter=1000)
        return implied_vol

    except ValueError:
        # If the solver fails, return a reasonable default volatility (small value)
        return 0.001
