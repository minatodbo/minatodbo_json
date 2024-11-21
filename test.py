def find_box_spreads(df):
    boxes = []  # List to store identified box spreads

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    # Loop through each group
    for (client, ticker, maturity), group in grouped:
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call'].sort_values('strike')
        puts = group[group['option_type'] == 'Put'].sort_values('strike')

        # Keep track of remaining quantities for each option leg
        remaining_quantities = group['quantity'].copy()

        # ---- Match Box Spreads ----
        for _, call_buy in calls.iterrows():
            if remaining_quantities[call_buy.name] <= 0:
                continue  # Skip if no remaining quantity to use

            # Match a short call with higher strike
            matching_calls = calls[(calls['strike'] > call_buy['strike'])]
            for _, call_sell in matching_calls.iterrows():
                if remaining_quantities[call_sell.name] >= 0:
                    continue  # Skip if no short call available

                # Match a short put at the lower strike
                matching_put_sells = puts[(puts['strike'] == call_buy['strike'])]
                for _, put_sell in matching_put_sells.iterrows():
                    if remaining_quantities[put_sell.name] >= 0:
                        continue  # Skip if no short put available

                    # Match a long put at the higher strike
                    matching_put_buys = puts[(puts['strike'] == call_sell['strike'])]
                    for _, put_buy in matching_put_buys.iterrows():
                        if remaining_quantities[put_buy.name] <= 0:
                            continue  # Skip if no long put available

                        # Calculate the box quantity as the minimum available across the four legs
                        box_quantity = min(
                            remaining_quantities[call_buy.name],
                            abs(remaining_quantities[call_sell.name]),
                            abs(remaining_quantities[put_sell.name]),
                            remaining_quantities[put_buy.name]
                        )

                        # Ensure we have a valid box spread
                        if box_quantity >= 1:
                            # Determine spread type
                            spread_type = 'Long Box Spread' if remaining_quantities[call_buy.name] > 0 else 'Short Box Spread'

                            # Add to result
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
                                'Spread Type': spread_type
                            })

                            # Deduct quantities from the legs
                            remaining_quantities[call_buy.name] -= box_quantity
                            remaining_quantities[call_sell.name] += box_quantity
                            remaining_quantities[put_sell.name] += box_quantity
                            remaining_quantities[put_buy.name] -= box_quantity

    return pd.DataFrame(boxes)
