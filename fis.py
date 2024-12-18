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
