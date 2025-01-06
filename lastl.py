import pandas as pd

# Assuming df is your dataframe

# Step 1: Create an empty list to store the count of box spreads per client and ticker
box_spread_counts = []

# Step 2: Group by Ticker and Client
for (ticker, client), group in df.groupby(['Ticker', 'Client']):
    
    # Step 3: Check if there are exactly 2 strikes and for each strike we need both call and put
    strikes = group['Strike'].unique()
    
    if len(strikes) == 2:  # Ensure we have 2 distinct strikes
        strike_data = group.groupby(['Strike', 'Option type']).agg({'Abs quantity': 'sum'}).reset_index()

        # Step 4: Ensure each strike has both a call and put, and 4 times the same absolute quantity
        strike_1 = strike_data[strike_data['Strike'] == strikes[0]]
        strike_2 = strike_data[strike_data['Strike'] == strikes[1]]

        if len(strike_1) == 2 and len(strike_2) == 2:
            strike_1_call = strike_1[strike_1['Option type'] == 'Call']['Abs quantity'].values
            strike_1_put = strike_1[strike_1['Option type'] == 'Put']['Abs quantity'].values

            strike_2_call = strike_2[strike_2['Option type'] == 'Call']['Abs quantity'].values
            strike_2_put = strike_2[strike_2['Option type'] == 'Put']['Abs quantity'].values

            # Step 5: Check that each leg has the same quantity and totals to 4
            if (len(strike_1_call) == 1 and len(strike_1_put) == 1 and 
                len(strike_2_call) == 1 and len(strike_2_put) == 1):
                abs_quantities = list(strike_1_call) + list(strike_1_put) + list(strike_2_call) + list(strike_2_put)
                
                if all(q == abs_quantities[0] for q in abs_quantities) and len(abs_quantities) == 4:
                    # Count this as one box spread for the current client and ticker
                    box_spread_counts.append((client, ticker))

# Step 6: Convert the result into a dataframe to get the count per client and ticker
box_spread_counts_df = pd.DataFrame(box_spread_counts, columns=['Client', 'Ticker'])

# Step 7: Group by Client and Ticker and count the occurrences of box spreads
box_spread_summary = box_spread_counts_df.groupby(['Client', 'Ticker']).size().reset_index(name='Box Spread Count')

# Step 8: Display the result
print(box_spread_summary)
