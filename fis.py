import numpy as np

def fx_swap_npv_dual(spot_rate, forward_rate, notional_usd, usd_rate, eur_rate, tenor):
    """
    Compute NPV of an FX Swap from both USD and EUR perspectives.
    
    Parameters:
    - spot_rate (float): Spot FX rate (EUR/USD).
    - forward_rate (float): Forward FX rate at maturity.
    - notional_usd (float): Notional amount in USD.
    - usd_rate (float): USD interest rate (annualized).
    - eur_rate (float): EUR interest rate (annualized).
    - tenor (float): Remaining tenor of the FX swap in days.
    
    Returns:
    - npv_usd (float): NPV of the FX swap in USD terms.
    - npv_eur (float): NPV of the FX swap in EUR terms.
    """
    # Convert rates to decimals
    usd_rate = usd_rate / 100
    eur_rate = eur_rate / 100
    
    # Compute the discount factors
    days_in_year = 360  # Market convention
    discount_usd = 1 / (1 + usd_rate * tenor / days_in_year)
    discount_eur = 1 / (1 + eur_rate * tenor / days_in_year)
    
    # Compute cashflows
    notional_eur = notional_usd / spot_rate  # Notional amount in EUR
    usd_forward_cashflow = notional_usd  # USD cashflow at forward date
    eur_forward_cashflow = notional_eur * forward_rate  # EUR cashflow at forward rate

    # Present value of cashflows
    pv_usd_cashflow = usd_forward_cashflow * discount_usd
    pv_eur_cashflow = eur_forward_cashflow * discount_eur

    # NPV from USD perspective
    npv_usd = pv_usd_cashflow - (pv_eur_cashflow / spot_rate)
    
    # NPV from EUR perspective
    npv_eur = (pv_usd_cashflow * spot_rate) - pv_eur_cashflow

    return npv_usd, npv_eur

# Example inputs
spot_rate = 1.0509          # Spot EUR/USD
forward_rate = 1.0548       # Forward EUR/USD
notional_usd = 100_000_000  # USD 100 million
usd_rate = 4.59             # USD interest rate (annualized in %)
eur_rate = 3.15             # EUR interest rate (annualized in %)
tenor = 30                  # Remaining tenor in days (e.g., 30 days)

# Compute NPV
npv_usd, npv_eur = fx_swap_npv_dual(spot_rate, forward_rate, notional_usd, usd_rate, eur_rate, tenor)

print(f"Net Present Value (NPV) of FX Swap:")
print(f"From USD Perspective: ${npv_usd:,.2f}")
print(f"From EUR Perspective: €{npv_eur:,.2f}")
