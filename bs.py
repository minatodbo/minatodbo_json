import numpy as np
import scipy.stats as si
from scipy import optimize

def calcimpliedvol_(S, K, T, r, marketoptionPrice, option_type):
    # Edge case for zero prices or strikes
    if S == 0 or K == 0:
        return 0
    if T == 0:
        T = 1  # Assume T = 1 year if T is 0

    # Calculate intrinsic value
    if option_type == "C":  # Call option
        intrinsic_value = max(S - K, 0)
    elif option_type == "P":  # Put option
        intrinsic_value = max(K - S, 0)
    else:
        raise ValueError("Option type must be 'C' or 'P'.")
    
    # Check if the market price is very close to the intrinsic value (deep ITM)
    deep_ITM_threshold = 0.01  # Tolerance for price being close to intrinsic value
    if abs(marketoptionPrice - intrinsic_value) < deep_ITM_threshold:
        # For deep ITM options, use a very wide volatility range
        min_volatility = 0.001  # Lower bound for volatility
        max_volatility = 200  # Upper bound for high volatility cases
    else:
        # For other options, we use a more conservative range
        min_volatility = 0.001
        max_volatility = 5
    
    try:
        # Black-Scholes pricing function
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
        
        # Using Brent's method to find the implied volatility
        implied_vol = optimize.brentq(bs_price, min_volatility, max_volatility, maxiter=1000)
        return implied_vol

    except ValueError:
        # In case the solver fails to converge, return a default volatility (e.g., 0.001)
        return 0.001
