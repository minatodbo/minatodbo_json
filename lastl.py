import pandas as pd
from itertools import combinations

# Assuming df is your dataframe with columns:
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
        
        if set(strike_1_data['Option type']) == {'Call', 'Put'} and set(strike_2_data['Option type']) == {'Call', 'Put'}:
            # Step 6: Extract the Abs quantity for both calls and puts for both strikes
            strike_1_call = strike_1_data[strike_1_data['Option type'] == 'Call']['Abs quantity'].values
            strike_1_put = strike_1_data[strike_1_data['Option type'] == 'Put']['Abs quantity'].values
            strike_2_call = strike_2_data[strike_2_data['Option type'] == 'Call']['Abs quantity'].values
            strike_2_put = strike_2_data[strike_2_data['Option type'] == 'Put']['Abs quantity'].values

            # Step 7: Ensure all four quantities are the same
            if len(strike_1_call) == 1 and len(strike_1_put) == 1 and len(strike_2_call) == 1 and len(strike_2_put) == 1:
                abs_quantities = [strike_1_call[0], strike_1_put[0], strike_2_call[0], strike_2_put[0]]
                
                # Check if all quantities are identical
                if abs_quantities[0] == abs_quantities[1] == abs_quantities[2] == abs_quantities[3]:
                    # Valid box spread found, record it
                    box_spread_counts.append((client, ticker, (strike_1, strike_2)))

# Step 8: Convert the list to a DataFrame
box_spread_counts_df = pd.DataFrame(box_spread_counts, columns=['Client', 'Ticker', 'Strike Pair'])

# Step 9: Group by Client and Ticker and count occurrences of box spreads
box_spread_summary = box_spread_counts_df.groupby(['Client', 'Ticker']).size().reset_index(name='Box Spread Count')

# Step 10: Display the result
print(box_spread_summary)
