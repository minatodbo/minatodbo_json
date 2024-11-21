import pandas as pd

def find_long_box_spreads(df):
    boxes = []  # List to store identified long box spreads
    remaining_quantities = df['quantity'].copy()  # Track the remaining quantities for each leg

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    for (client, ticker, maturity), group in grouped:
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call'].sort_values('strike')
        puts = group[group['option_type'] == 'Put'].sort_values('strike')

        # ---- Long Box Spread Identification ----
        for _, call_buy in calls.iterrows():
            if remaining_quantities[call_buy.name] <= 0:
                continue  # Skip if no remaining long call quantity

            # Match a short call with a higher strike
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
                            abs(remaining_quantities[call_buy.name]),
                            abs(remaining_quantities[call_sell.name]),
                            abs(remaining_quantities[put_sell.name]),
                            abs(remaining_quantities[put_buy.name])
                        )

                        # Add the long box spread to results
                        if box_quantity > 0:
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

                            # Deduct quantities from the legs (subtract the quantity from long legs and add to short legs)
                            remaining_quantities[call_buy.name] -= box_quantity
                            remaining_quantities[call_sell.name] += box_quantity
                            remaining_quantities[put_sell.name] += box_quantity
                            remaining_quantities[put_buy.name] -= box_quantity

    return boxes, remaining_quantities


def find_short_box_spreads(df, remaining_quantities):
    boxes = []  # List to store identified short box spreads

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    for (client, ticker, maturity), group in grouped:
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call'].sort_values('strike')
        puts = group[group['option_type'] == 'Put'].sort_values('strike')

        # ---- Short Box Spread Identification ----
        for _, call_sell in calls.iterrows():
            if remaining_quantities[call_sell.name] >= 0:
                continue  # Skip if no remaining short call quantity

            # Match a long call with a higher strike
            for _, call_buy in calls.iterrows():
                if call_buy['strike'] <= call_sell['strike'] or remaining_quantities[call_buy.name] <= 0:
                    continue  # Skip if not a higher strike or no remaining long call quantity

                # Match a long put at the lower strike
                for _, put_buy in puts.iterrows():
                    if put_buy['strike'] != call_sell['strike'] or remaining_quantities[put_buy.name] <= 0:
                        continue  # Skip if not matching the lower strike or no remaining long put quantity

                    # Match a short put at the higher strike
                    for _, put_sell in puts.iterrows():
                        if put_sell['strike'] != call_buy['strike'] or remaining_quantities[put_sell.name] >= 0:
                            continue  # Skip if not matching the higher strike or no remaining short put quantity

                        # Calculate the box quantity as the minimum available across the four legs
                        box_quantity = min(
                            abs(remaining_quantities[call_sell.name]),
                            abs(remaining_quantities[call_buy.name]),
                            abs(remaining_quantities[put_buy.name]),
                            abs(remaining_quantities[put_sell.name])
                        )

                        # Add the short box spread to results
                        if box_quantity > 0:
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
                                'Spread Type': 'Short Box Spread'
                            })

                            # Deduct quantities from the legs (subtract the quantity from long legs and add to short legs)
                            remaining_quantities[call_buy.name] -= box_quantity
                            remaining_quantities[call_sell.name] += box_quantity
                            remaining_quantities[put_sell.name] += box_quantity
                            remaining_quantities[put_buy.name] -= box_quantity

    return boxes, remaining_quantities


def find_box_spreads(df):
    # Step 1: Find long box spreads
    long_boxes, remaining_quantities = find_long_box_spreads(df)
    
    # Step 2: Find short box spreads based on remaining quantities after long spreads are found
    short_boxes, _ = find_short_box_spreads(df, remaining_quantities)

    # Combine the long and short boxes into one list
    all_boxes = long_boxes + short_boxes

    return pd.DataFrame(all_boxes)


# Test data with quantities that will produce both long and short spreads
data = {
    'client': ['ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA', 'ClientA'],
    'ticker': ['ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC'],
    'underlying_price': [100, 100, 100, 100, 100, 100, 100, 100],
    'quantity': [-5, 5, 5, -5, 10, -10, -10, 10],  # 5 for long and 10 for short
    'strike': [95, 105, 105, 95, 95, 105, 105, 95],
    'option_type': ['Call', 'Call', 'Put', 'Put', 'Call', 'Call', 'Put', 'Put'],
    'maturity': ['2024-12-31'] * 8,
}

df = pd.DataFrame(data)

# Run the function
box_spreads_df = find_box_spreads(df)
print("\nIdentified Box Spreads:")
print(box_spreads_df)
