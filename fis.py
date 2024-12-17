import numpy as np

def fx_swap_npv_lend_usd_borrow_eur(spot_rate, forward_points, notional_eur, usd_rate_bid, usd_rate_ask, eur_rate_bid, eur_rate_ask, tenor):
    """
    Compute NPV of an FX Swap where USD is lent and EUR is borrowed with fixed EUR notional.
    
    Parameters:
    - spot_rate (float): Spot FX rate (EUR/USD).
    - forward_points (float): Forward points to add to the spot rate.
    - notional_eur (float): Fixed EUR notional amount.
    - usd_rate_bid (float): USD bid interest rate (annualized, %).
    - usd_rate_ask (float): USD ask interest rate (annualized, %).
    - eur_rate_bid (float): EUR bid interest rate (annualized, %).
    - eur_rate_ask (float): EUR ask interest rate (annualized, %).
    - tenor (float): Remaining tenor in days.
    
    Returns:
    - NPV from USD perspective.
    - NPV from EUR perspective.
    """
    # Convert annualized rates to decimals
    usd_rate_bid_decimal = usd_rate_bid / 100
    usd_rate_ask_decimal = usd_rate_ask / 100
    eur_rate_bid_decimal = eur_rate_bid / 100
    eur_rate_ask_decimal = eur_rate_ask / 100
    
    # Calculate forward rate
    forward_rate = spot_rate + forward_points / 10000  # Convert forward points to decimal
    
    # Calculate USD amounts at t=0 and T
    usd_amount_t0 = notional_eur * spot_rate
    usd_amount_tT = notional_eur * forward_rate
    
    # Discount factors
    days_in_year = 360  # Market convention for FX swaps
    df_usd_bid = 1 / (1 + usd_rate_bid_decimal * tenor / days_in_year)
    df_usd_ask = 1 / (1 + usd_rate_ask_decimal * tenor / days_in_year)
    df_eur_bid = 1 / (1 + eur_rate_bid_decimal * tenor / days_in_year)
    df_eur_ask = 1 / (1 + eur_rate_ask_decimal * tenor / days_in_year)
    
    # Present value of USD cash flows
    pv_usd_outflow = usd_amount_t0 * df_usd_ask
    pv_usd_inflow = usd_amount_tT * df_usd_bid
    
    # Present value of EUR cash flows
    pv_eur_outflow = notional_eur * df_eur_ask
    pv_eur_inflow = notional_eur * df_eur_bid  # Same amount at t=0 and T
    
    # NPV calculations
    npv_usd_perspective = pv_usd_inflow - pv_usd_outflow
    npv_eur_perspective = pv_eur_inflow - pv_eur_outflow
    
    return npv_usd_perspective, npv_eur_perspective

# Example usage
spot_rate = 1.0509          # Spot EUR/USD
forward_points = 0.39       # Forward points (e.g., 0.39 in market quotes)
notional_eur = 100_000_000  # EUR 100 million
usd_rate_bid = 4.53         # USD bid interest rate (% annualized)
usd_rate_ask = 4.59         # USD ask interest rate (% annualized)
eur_rate_bid = 3.08         # EUR bid interest rate (% annualized)
eur_rate_ask = 3.15         # EUR ask interest rate (% annualized)
tenor = 30                  # Remaining tenor in days

npv_usd, npv_eur = fx_swap_npv_lend_usd_borrow_eur(spot_rate, forward_points, notional_eur, usd_rate_bid, usd_rate_ask, eur_rate_bid, eur_rate_ask, tenor)
print(f"NPV from USD perspective: ${npv_usd:,.2f}")
print(f"NPV from EUR perspective: €{npv_eur:,.2f}")
