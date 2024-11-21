def find_box_spreads(df):
    boxes = []  # List to store identified box spreads

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    for (client, ticker, maturity), group in grouped:
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call'].sort_values('strike')
        puts = group[group['option_type'] == 'Put'].sort_values('strike')

        # Create a copy to track remaining quantities
        remaining_quantities = group['quantity'].copy()

        # ---- Match Box Spreads ----
        for _, call_buy in calls.iterrows():
            if remaining_quantities[call_buy.name] <= 0:
                continue  # Skip if no remaining long call quantity

            # Match a short call with higher strike
            for _, call_sell in calls.iterrows():
                if call_sell['strike'] <= call_buy['strike'] or remaining_quantities[call_sell.name] >= 0:
                    continue  # Skip if not a higher strike or no remaining short call quantity

                # Match a short put at the lower strike
                for _, put_sell in puts.iterrows():
                    if put_sell['strike'] != call_buy['strike'] or remaining_quantities[put_sell.name] >= 0:
                        continue  # Skip if not matching the lower strike or no remaining short put quantity

                    # Match a long put at the higher strike
                    for _, put_buy in puts.iterrows():
                        if put_buy['strike'] != call_sell['strike'] or remaining_quantities[put_buy.name] <= 0:
                            continue  # Skip if not matching the higher strike or no remaining long put quantity

                        # Calculate the box quantity as the minimum available across the four legs
                        box_quantity = min(
                            remaining_quantities[call_buy.name],
                            abs(remaining_quantities[call_sell.name]),
                            abs(remaining_quantities[put_sell.name]),
                            remaining_quantities[put_buy.name]
                        )

                        # Determine the spread type based on call_buy direction
                        spread_type = 'Long Box Spread' if call_buy['quantity'] > 0 else 'Short Box Spread'

                        # Add the box spread to results
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

                        # Exit loops to avoid double-counting
                        break

    return pd.DataFrame(boxes)
