import pandas as pd
from itertools import combinations

# Assuming df is your dataframe with the columns:
# 'Quantity', 'Abs quantity', 'Ticker', 'Strike', 'Client', 'Option type'

# Create an empty list to store valid box spreads
box_spread_counts = []

# Step 1: Group by Ticker and Client
for (ticker, client), group in df.groupby(['Ticker', 'Client']):
    # Step 2: Get all unique strikes for the current client and ticker
    strikes = group['Strike'].unique()

    # Step 3: Iterate over all pairs of strikes (combinations of 2 strikes)
    for strike_1, strike_2 in combinations(strikes, 2):
        # Step 4: Get the options data for both strikes (Call and Put)
        strike_data = group[group['Strike'].isin([strike_1, strike_2])]
        
        # Step 5: Ensure we have both Call and Put options for both strikes
        strike_1_data = strike_data[strike_data['Strike'] == strike_1]
        strike_2_data = strike_data[strike_data['Strike'] == strike_2]
        
        # Ensure both strikes have a Call and Put option
        if set(strike_1_data['Option type']) == {'Call', 'Put'} and set(strike_2_data['Option type']) == {'Call', 'Put'}:
            
            # Step 6: Extract the Abs quantity for both calls and puts for both strikes
            strike_1_call = strike_1_data[strike_1_data['Option type'] == 'Call']
            strike_1_put = strike_1_data[strike_1_data['Option type'] == 'Put']
            strike_2_call = strike_2_data[strike_2_data['Option type'] == 'Call']
            strike_2_put = strike_2_data[strike_2_data['Option type'] == 'Put']
            
            # Step 7: Ensure we have exactly 1 of each type of option for both strikes
            if len(strike_1_call) == 1 and len(strike_1_put) == 1 and len(strike_2_call) == 1 and len(strike_2_put) == 1:
                
                # Extract quantities
                abs_quantities = [
                    strike_1_call['Abs quantity'].values[0],
                    strike_1_put['Abs quantity'].values[0],
                    strike_2_call['Abs quantity'].values[0],
                    strike_2_put['Abs quantity'].values[0]
                ]
                
                # Check if all quantities match
                if abs_quantities[0] == abs_quantities[1] == abs_quantities[2] == abs_quantities[3]:
                    # If the quantities match, check the positions (long vs short)
                    # For a long box spread, the positions will be:
                    # Long Call at lower strike, Short Call at higher strike
                    # Long Put at lower strike, Short Put at higher strike
                    
                    # For short box spread, the positions will be the opposite.
                    # Short Call at lower strike, Long Call at higher strike
                    # Short Put at lower strike, Long Put at higher strike
                    
                    # Assuming the positions in the dataframe indicate long or short explicitly
                    if (strike_1_call['Quantity'].values[0] > 0 and strike_2_call['Quantity'].values[0] < 0 and 
                        strike_1_put['Quantity'].values[0] > 0 and strike_2_put['Quantity'].values[0] < 0):
                        # It's a **long box spread**
                        box_spread_counts.append(('Long', client, ticker))
                    elif (strike_1_call['Quantity'].values[0] < 0 and strike_2_call['Quantity'].values[0] > 0 and
                          strike_1_put['Quantity'].values[0] < 0 and strike_2_put['Quantity'].values[0] > 0):
                        # It's a **short box spread**
                        box_spread_counts.append(('Short', client, ticker))

# Step 8: Convert the list to a DataFrame
box_spread_counts_df = pd.DataFrame(box_spread_counts, columns=['Position', 'Client', 'Ticker'])

# Step 9: Group by Client, Ticker, and Position, and count occurrences of box spreads
box_spread_summary = box_spread_counts_df.groupby(['Client', 'Ticker', 'Position']).size().reset_index(name='Box Spread Count')

# Step 10: Display the result
print(box_spread_summary)
