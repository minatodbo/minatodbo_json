from datetime import timedelta
import numpy as np

# Inputs
initial_spot = 1.07  # Spot rate at t=0
initial_forward = 1.08  # Forward rate agreed at t=0
current_spot = 1.05  # Current spot rate
current_forward = 1.06  # Current forward rate
usd_rate = 4.30 / 100  # USD interest rate (annualized)
eur_rate = 3.00 / 100  # EUR interest rate (annualized)
notional_eur = 1_000_000  # EUR notional amount (constant)
days_remaining = 30  # Time to maturity in days
days_in_year = 360  # Day count convention

# Time factor for discounting
time_to_maturity = days_remaining / days_in_year

# Calculate initial USD notional at t=0
initial_usd_notional = notional_eur * initial_spot

# Calculate USD amount to be received at maturity (based on initial forward rate)
usd_receivable_at_maturity = notional_eur * initial_forward

# Current value of USD receivable (discounted at USD rate)
usd_leg_value = usd_receivable_at_maturity / (1 + usd_rate * time_to_maturity)

# Current value of EUR repayment (discounted at EUR rate)
eur_leg_value = notional_eur / (1 + eur_rate * time_to_maturity)

# Current EUR value of the USD leg (based on current forward rate)
usd_leg_value_in_eur = usd_leg_value / current_forward

# NPV calculation (EUR perspective)
npv_eur = usd_leg_value_in_eur - eur_leg_value

# NPV calculation (USD perspective)
npv_usd = npv_eur * current_spot

# Output results
print("NPV (EUR perspective): {:.2f} EUR".format(npv_eur))
print("NPV (USD perspective): {:.2f} USD".format(npv_usd))


def calculate_mtm_fx_swap(initial_spot, initial_forward, current_spot, current_forward, 
                          notional_usd, usd_rate, eur_rate, days_to_maturity, days_in_year=360):
    """
    Calculate the MTM of an FX swap from both USD and EUR perspectives.
    
    Parameters:
    - initial_spot: Spot rate at inception of the swap.
    - initial_forward: Forward rate agreed upon at inception.
    - current_spot: Current spot rate.
    - current_forward: Current forward rate.
    - notional_usd: Notional amount lent in USD.
    - usd_rate: USD interest rate (annualized, as a percentage).
    - eur_rate: EUR interest rate (annualized, as a percentage).
    - days_to_maturity: Remaining days until the swap matures.
    - days_in_year: Number of days in a year (360 by default for FX conventions).
    
    Returns:
    - MTM value from both USD and EUR perspectives.
    """
    # Convert rates from percentages to decimals
    usd_rate /= 100
    eur_rate /= 100
    
    # Calculate the initial EUR notional (based on initial spot rate)
    notional_eur = notional_usd / initial_spot

    # Discount factors for USD and EUR (using current market rates)
    discount_factor_usd = 1 / (1 + usd_rate * days_to_maturity / days_in_year)
    discount_factor_eur = 1 / (1 + eur_rate * days_to_maturity / days_in_year)
    
    # Calculate the USD and EUR cash flows at maturity based on the initial forward
    usd_cash_flow = notional_usd  # USD leg doesn't change
    eur_cash_flow = notional_eur * initial_forward  # EUR leg at inception forward rate

    # Current value of USD and EUR legs
    usd_leg_mtm = usd_cash_flow * discount_factor_usd
    eur_leg_mtm = eur_cash_flow * discount_factor_eur / current_spot  # Convert EUR to USD using current spot

    # MTM value (USD perspective)
    mtm_usd = usd_leg_mtm - eur_leg_mtm

    # MTM value (EUR perspective)
    eur_leg_mtm_eur = eur_cash_flow * discount_factor_eur  # In EUR terms
    usd_leg_mtm_eur = usd_cash_flow * discount_factor_usd * current_spot  # Convert USD to EUR using current spot
    mtm_eur = eur_leg_mtm_eur - usd_leg_mtm_eur

    return mtm_usd, mtm_eur


# Example inputs (same as discussed):
initial_spot = 1.07
initial_forward = 1.08
current_spot = 1.05
current_forward = 1.06
notional_usd = 100_000_000  # USD 100 million
usd_rate = 4.30  # 4.30% annualized
eur_rate = 3.00  # 3.00% annualized
days_to_maturity = 30  # Remaining days to maturity

# Calculate MTM
mtm_usd, mtm_eur = calculate_mtm_fx_swap(initial_spot, initial_forward, current_spot, current_forward, 
                                         notional_usd, usd_rate, eur_rate, days_to_maturity)

# Print results
print(f"MTM (USD Perspective): ${mtm_usd:,.2f}")
print(f"MTM (EUR Perspective): €{mtm_eur:,.2f}")

from math import exp

# Inputs
notional_usd = 100_000_000  # USD notional
initial_spot = 1.07  # Spot rate at inception
initial_forward = 1.08  # Forward rate at inception
current_spot = 1.05  # Current spot rate
current_forward = 1.06  # Current forward rate
usd_rate = 0.045  # Current USD annual rate (e.g., 4.5%)
eur_rate = 0.031  # Current EUR annual rate (e.g., 3.1%)
days_to_maturity = 30  # Days remaining to maturity
original_tenor = 60  # Total tenor of the swap in days

# Derived Inputs
notional_eur = notional_usd / initial_spot  # EUR notional fixed at inception

# Discount factors
usd_discount = exp(-usd_rate * days_to_maturity / 360)
eur_discount = exp(-eur_rate * days_to_maturity / 360)

# USD leg value
usd_leg_value = notional_usd * usd_discount  # USD notional discounted to present

# EUR leg value
eur_leg_value_in_eur = notional_eur * eur_discount  # EUR notional discounted to present
eur_leg_value_in_usd = eur_leg_value_in_eur / current_spot  # Converted to USD

# MTM (USD perspective)
mtm = usd_leg_value - eur_leg_value_in_usd

# Output
print(f"USD Leg Value: {usd_leg_value:,.2f} USD")
print(f"EUR Leg Value: {eur_leg_value_in_usd:,.2f} USD (converted from EUR)")
print(f"Mark-to-Market (MTM): {mtm:,.2f} USD")

