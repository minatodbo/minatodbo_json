import pandas as pd

def find_box_spreads(df):
    boxes = []  # List to store identified box spreads

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

        print(f"\nProcessing group: {client}, {ticker}, {maturity}")
        print(f"Calls:\n{calls[['strike', 'quantity']]}")
        print(f"Puts:\n{puts[['strike', 'quantity']]}")

        # ---- Long Box Spread Identification ----
        used_options = []  # Track options used in spreads

        for _, call_buy in calls.iterrows():
            if call_buy['quantity'] <= 0 or call_buy.name in used_options:
                continue

            # Match with a short call at a higher strike
            matching_calls = calls[(calls['strike'] > call_buy['strike']) & (calls['quantity'] < 0) & (~calls.index.isin(used_options))]

            for _, call_sell in matching_calls.iterrows():
                # Match a short put at the lower strike
                matching_put_sells = puts[(puts['strike'] == call_buy['strike']) & (puts['quantity'] < 0) & (~puts.index.isin(used_options))]

                for _, put_sell in matching_put_sells.iterrows():
                    # Match a long put at the higher strike
                    matching_put_buys = puts[(puts['strike'] == call_sell['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

                    for _, put_buy in matching_put_buys.iterrows():
                        # Calculate box quantity
                        box_quantity = min(
                            call_buy['quantity'],
                            abs(call_sell['quantity']),
                            abs(put_sell['quantity']),
                            put_buy['quantity']
                        )

                        if box_quantity >= 5:  # Minimum quantity for valid box spread
                            boxes.append({
                                'Client': client,
                                'Ticker': ticker,
                                'Maturity': maturity,
                                'Buy Call Strike': call_buy['strike'],
                                'Sell Call Strike': call_sell['strike'],
                                'Sell Put Strike': put_sell['strike'],
                                'Buy Put Strike': put_buy['strike'],
                                'Underlying Price': call_buy['underlying_price'],
                                'Box Quantity': box_quantity,
                                'Spread Type': 'Long Box Spread'
                            })

                            used_options.extend([call_buy.name, call_sell.name, put_sell.name, put_buy.name])

                            # Update quantities
                            df.loc[call_buy.name, 'quantity'] -= box_quantity
                            df.loc[call_sell.name, 'quantity'] += box_quantity
                            df.loc[put_sell.name, 'quantity'] += box_quantity
                            df.loc[put_buy.name, 'quantity'] -= box_quantity

        # ---- Short Box Spread Identification ----
        for _, call_sell in calls.iterrows():
            if call_sell['quantity'] >= 0 or call_sell.name in used_options:
                continue

            # Match with a long call at a higher strike
            matching_calls = calls[(calls['strike'] > call_sell['strike']) & (calls['quantity'] > 0) & (~calls.index.isin(used_options))]

            for _, call_buy in matching_calls.iterrows():
                # Match a long put at the lower strike
                matching_put_buys = puts[(puts['strike'] == call_sell['strike']) & (puts['quantity'] > 0) & (~puts.index.isin(used_options))]

                for _, put_buy in matching_put_buys.iterrows():
                    # Match a short put at the higher strike
                    matching_put_sells = puts[(puts['strike'] == call_buy['strike']) & (puts['quantity'] < 0) & (~puts.index.isin(used_options))]

                    for _, put_sell in matching_put_sells.iterrows():
                        # Calculate box quantity
                        box_quantity = min(
                            abs(call_sell['quantity']),
                            call_buy['quantity'],
                            put_buy['quantity'],
                            abs(put_sell['quantity'])
                        )

                        if box_quantity >= 5:  # Minimum quantity for valid box spread
                            boxes.append({
                                'Client': client,
                                'Ticker': ticker,
                                'Maturity': maturity,
                                'Sell Call Strike': call_sell['strike'],
                                'Buy Call Strike': call_buy['strike'],
                                'Buy Put Strike': put_buy['strike'],
                                'Sell Put Strike': put_sell['strike'],
                                'Underlying Price': call_sell['underlying_price'],
                                'Box Quantity': box_quantity,
                                'Spread Type': 'Short Box Spread'
                            })

                            used_options.extend([call_sell.name, call_buy.name, put_buy.name, put_sell.name])

                            # Update quantities
                            df.loc[call_sell.name, 'quantity'] += box_quantity
                            df.loc[call_buy.name, 'quantity'] -= box_quantity
                            df.loc[put_buy.name, 'quantity'] -= box_quantity
                            df.loc[put_sell.name, 'quantity'] += box_quantity

    return pd.DataFrame(boxes)
