from xbbg import blp
import pandas as pd

# Fetching spot and basis data for EUR/USD (example)
spot_data = blp.bdh(['EURUSD Curncy'], 'PX_LAST', '2024-12-01', '2024-12-10')
fwd_points = blp.bdp('EURUSD Curncy', 'FWD_POINTS')

# Fetching interest rates for USD and EUR (e.g., 1 month for EUR/USD)
usd_rate = blp.bdp('US0001M Index', 'LAST_PRICE')  # 1-month USD rate
eur_rate = blp.bdp('EUR001M Index', 'LAST_PRICE')  # 1-month EUR rate

# Fetching the cross-currency basis swap spread
basis_swap_spread = blp.bdp('EURUSD Curncy', 'SWAP_BASIS')

# Printing fetched data
print(f"Spot Data: \n{spot_data.tail()}")
print(f"Forward Points: {fwd_points}")
print(f"USD Rate: {usd_rate}")
print(f"EUR Rate: {eur_rate}")
print(f"Basis Swap Spread: {basis_swap_spread}")

# Now let's calculate the cross-currency swap basis spread
# We need the forward rate (calculated from spot + forward points) and interest rates for EUR and USD

spot = spot_data['PX_LAST'].iloc[-1]  # Latest spot rate
forward_rate = spot + fwd_points / 10000  # Adjust forward points to the spot rate (dividing by 10000)

# Calculate the forward-implied rate differential
forward_implied_diff = (forward_rate - spot) / spot * 100  # In percentage terms

# Calculate the actual interest rate differential
actual_rate_diff = usd_rate - eur_rate  # USD rate minus EUR rate

# Cross-currency basis is the difference between the implied forward rate differential and the actual interest rate differential
cross_currency_basis = forward_implied_diff - actual_rate_diff

print(f"Calculated Cross-Currency Basis: {cross_currency_basis:.4f} bps")
