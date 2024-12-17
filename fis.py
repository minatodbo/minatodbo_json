import numpy as np

def fx_swap_npv(
    notional_usd, notional_eur, 
    initial_spot_rate, initial_forward_rate, 
    current_spot_rate, current_forward_points, 
    usd_rate, eur_rate, 
    days_remaining
):
    """
    Calculate the NPV of an FX swap given initial and current market conditions.
    
    Parameters:
    - notional_usd (float): Initial USD notional amount.
    - notional_eur (float): Initial EUR notional amount.
    - initial_spot_rate (float): Spot rate at initiation (EUR/USD).
    - initial_forward_rate (float): Forward rate agreed at initiation.
    - current_spot_rate (float): Current spot rate (EUR/USD).
    - current_forward_points (float): Current forward points for the remaining period.
    - usd_rate (float): Current USD interest rate (annualized, %).
    - eur_rate (float): Current EUR interest rate (annualized, %).
    - days_remaining (int): Days remaining until maturity.
    
    Returns:
    - npv_usd (float): NPV from the USD perspective.
    - npv_eur (float): NPV from the EUR perspective.
    """
    # Convert annualized rates to decimals
    usd_rate_decimal = usd_rate / 100
    eur_rate_decimal = eur_rate / 100
    
    # Calculate current forward rate for the remaining period
    current_forward_rate = current_spot_rate + current_forward_points / 10000  # Convert points to decimal
    
    # Calculate discount factors for the remaining period
    days_in_year = 360  # Market convention for FX swaps
    df_usd = 1 / (1 + usd_rate_decimal * days_remaining / days_in_year)
    df_eur = 1 / (1 + eur_rate_decimal * days_remaining / days_in_year)
    
    # Calculate the value of the final exchange at maturity
    final_usd_payment = notional_eur * initial_forward_rate
    final_eur_payment = notional_usd / initial_forward_rate
    
    # Present value of the final cash flows
    pv_final_usd_payment = final_usd_payment * df_usd
    pv_final_eur_payment = final_eur_payment * df_eur
    
    # NPV calculations
    npv_usd = pv_final_usd_payment - notional_usd
    npv_eur = pv_final_eur_payment - notional_eur
    
    return npv_usd, npv_eur

# Example usage
notional_usd = 105_090_000  # USD amount at initiation
notional_eur = 100_000_000  # EUR amount at initiation
initial_spot_rate = 1.0509  # Spot rate at initiation
initial_forward_rate = 1.0548  # Forward rate agreed at initiation
current_spot_rate = 1.0600  # Current spot rate
current_forward_points = 0.40  # Current forward points for remaining period
usd_rate = 4.59  # Current USD interest rate (% annualized)
eur_rate = 3.15  # Current EUR interest rate (% annualized)
days_remaining = 30  # Days remaining until maturity

npv_usd, npv_eur = fx_swap_npv(
    notional_usd, notional_eur, 
    initial_spot_rate, initial_forward_rate, 
    current_spot_rate, current_forward_points, 
    usd_rate, eur_rate, 
    days_remaining
)

print(f"NPV from USD perspective: ${npv_usd:,.2f}")
print(f"NPV from EUR perspective: €{npv_eur:,.2f}")
