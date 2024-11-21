import pandas as pd

def find_strategies(df):
    strategies = []  # List to store identified strategies

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    # Loop through each group
    for (client, ticker, maturity), group in grouped:
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call']
        puts = group[group['option_type'] == 'Put']

        # Sort by strike price for both calls and puts
        calls = calls.sort_values('strike')
        puts = puts.sort_values('strike')

        # Display for debugging
        print(f"\nProcessing group: {client}, {ticker}, {maturity}")
        print(f"Calls:\n{calls[['strike', 'quantity']]}")
        print(f"Puts:\n{puts[['strike', 'quantity']]}")

        used_options = []  # To track options already used in spreads

        # ---- Long Box Spread Identification ----
        for i, call_buy in calls.iterrows():
            if call_buy['quantity'] <= 0 or call_buy.name in used_options:
                continue  # Skip if not a long call or already used

            # Match it with a short call with a higher strike
            matching_calls = calls[(calls['strike'] > call_buy['strike']) & (calls['quantity'] < 0) & (~calls.index.isin(used_options))]

            for _, call_sell in matching_calls.iterrows():
                # Match long puts for the long box spread
                matching_puts = puts[(puts['strike'] == call_buy['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

                for _, put_buy in matching_puts.iterrows():
                    # Match short puts for the long box spread
                    matching_put_sells = puts[(puts['strike'] == call_sell['strike']) & (puts['quantity'] < 0) & (~puts.index.isin(used_options))]

                    for _, put_sell in matching_put_sells.iterrows():
                        # Calculate the box quantity as the minimum of the matching quantities
                        box_quantity = min(
                            call_buy['quantity'],
                            abs(call_sell['quantity']),
                            put_buy['quantity'],
                            abs(put_sell['quantity'])
                        )

                        # Only add valid box spreads (with quantity >= 5)
                        if box_quantity >= 5:  # Ensure box spread has enough quantity
                            strategies.append({
                                'Client': client,
                                'Ticker': ticker,
                                'Maturity': maturity,
                                'Buy Call Strike': call_buy['strike'],
                                'Sell Call Strike': call_sell['strike'],
                                'Buy Put Strike': put_buy['strike'],
                                'Sell Put Strike': put_sell['strike'],
                                'Underlying Price': call_buy['underlying_price'],
                                'Box Quantity': box_quantity,
                                'Spread Type': 'Long Box Spread'
                            })

                            # Mark options as used
                            used_options.extend([call_buy.name, call_sell.name, put_buy.name, put_sell.name])

                            # Update quantities after identifying the spread
                            df.loc[call_buy.name, 'quantity'] -= box_quantity
                            df.loc[call_sell.name, 'quantity'] += box_quantity
                            df.loc[put_buy.name, 'quantity'] -= box_quantity
                            df.loc[put_sell.name, 'quantity'] += box_quantity

        # ---- Short Box Spread Identification ----
        for i, call_sell in calls.iterrows():
            if call_sell['quantity'] >= 0 or call_sell.name in used_options:
                continue  # Skip if not a short call or already used

            # Match it with a long call with a higher strike
            matching_calls = calls[(calls['strike'] > call_sell['strike']) & (calls['quantity'] > 0) & (~calls.index.isin(used_options))]

            for _, call_buy in matching_calls.iterrows():
                # Match short puts for the short box spread
                matching_puts = puts[(puts['strike'] == call_sell['strike']) & (puts['quantity'] < 0) & (~puts.index.isin(used_options))]

                for _, put_sell in matching_puts.iterrows():
                    # Match long puts for the short box spread
                    matching_put_buys = puts[(puts['strike'] == call_buy['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

                    for _, put_buy in matching_put_buys.iterrows():
                        # Calculate the box quantity as the minimum of the matching quantities
                        box_quantity = min(
                            abs(call_sell['quantity']),
                            call_buy['quantity'],
                            abs(put_sell['quantity']),
                            put_buy['quantity']
                        )

                        # Only add valid box spreads (with quantity >= 5)
                        if box_quantity >= 5:  # Ensure box spread has enough quantity
                            strategies.append({
                                'Client': client,
                                'Ticker': ticker,
                                'Maturity': maturity,
                                'Buy Call Strike': call_buy['strike'],
                                'Sell Call Strike': call_sell['strike'],
                                'Buy Put Strike': put_buy['strike'],
                                'Sell Put Strike': put_sell['strike'],
                                'Underlying Price': call_buy['underlying_price'],
                                'Box Quantity': box_quantity,
                                'Spread Type': 'Short Box Spread'
                            })

                            # Mark options as used
                            used_options.extend([call_buy.name, call_sell.name, put_buy.name, put_sell.name])

                            # Update quantities after identifying the spread
                            df.loc[call_buy.name, 'quantity'] -= box_quantity
                            df.loc[call_sell.name, 'quantity'] += box_quantity
                            df.loc[put_buy.name, 'quantity'] -= box_quantity
                            df.loc[put_sell.name, 'quantity'] += box_quantity

        # ---- Straddle Identification ----
        for i, call in calls.iterrows():
            if call['quantity'] <= 0 or call.name in used_options:
                continue

            matching_puts = puts[(puts['strike'] == call['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

            for _, put in matching_puts.iterrows():
                straddle_quantity = min(call['quantity'], put['quantity'])

                if straddle_quantity > 0:
                    strategies.append({
                        'Client': client,
                        'Ticker': ticker,
                        'Maturity': maturity,
                        'Buy Call Strike': call['strike'],
                        'Sell Call Strike': call['strike'],
                        'Buy Put Strike': put['strike'],
                        'Sell Put Strike': put['strike'],
                        'Underlying Price': call['underlying_price'],
                        'Straddle Quantity': straddle_quantity,
                        'Spread Type': 'Straddle'
                    })

                    used_options.extend([call.name, put.name])

        # ---- Strangle Identification ----
        for i, call in calls.iterrows():
            if call['quantity'] <= 0 or call.name in used_options:
                continue

            matching_puts = puts[(puts['strike'] > call['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

            for _, put in matching_puts.iterrows():
                strangle_quantity = min(call['quantity'], put['quantity'])

                if strangle_quantity > 0:
                    strategies.append({
                        'Client': client,
                        'Ticker': ticker,
                        'Maturity': maturity,
                        'Buy Call Strike': call['strike'],
                        'Sell Call Strike': call['strike'],
                        'Buy Put Strike': put['strike'],
                        'Sell Put Strike': put['strike'],
                        'Underlying Price': call['underlying_price'],
                        'Strangle Quantity': strangle_quantity,
                        'Spread Type': 'Strangle'
                    })

                    used_options.extend([call.name, put.name])

    return pd.DataFrame(strategies)


# Test data for identifying the strategies
data = {
    'client': ['ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA'],
    'ticker': ['ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC'],
    'underlying_price': [100, 100, 100, 100, 100, 100, 100, 100],
    'quantity': [-5, 5, 5, -5, 5, -5, -5, 1],  # Example quantities
    'strike': [95, 105, 105, 95, 95, 105, 105, 95],
    'option_type': ['Call', 'Call', 'Put', 'Put', 'Call', 'Call', 'Put', 'Put'],
    'maturity': ['2024-12-31'] * 8,
}

df = pd.DataFrame(data)

# Find strategies
strategies_df = find_strategies(df)

# Display identified strategies
print("\nIdentified Strategies:")
print(strategies_df)
