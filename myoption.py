import pandas as pd

def find_box_spreads(df):
    boxes = []  # List to store identified box spreads
    remaining_quantities = df['quantity'].copy()  # Track the remaining quantities for each leg

    # Group by client, ticker, and maturity
    grouped = df.groupby(['client', 'ticker', 'maturity'])

    # Loop through each group
    for (client, ticker, maturity), group in grouped:
        print(f"\nProcessing group: {client}, {ticker}, {maturity}")
        
        # Separate calls and puts
        calls = group[group['option_type'] == 'Call'].sort_values('strike')
        puts = group[group['option_type'] == 'Put'].sort_values('strike')

        print(f"Calls:\n{calls[['strike', 'quantity']]}")
        print(f"Puts:\n{puts[['strike', 'quantity']]}")

        # ---- Identify Long Box Spreads ----
        identify_spread(client, ticker, maturity, calls, puts, remaining_quantities, boxes, spread_type="Long")

        # ---- Identify Short Box Spreads ----
        identify_spread(client, ticker, maturity, calls, puts, remaining_quantities, boxes, spread_type="Short")

    return pd.DataFrame(boxes)


def identify_spread(client, ticker, maturity, calls, puts, remaining_quantities, boxes, spread_type="Long"):
    if spread_type == "Long":
        sign = 1
        opposite_sign = -1
    elif spread_type == "Short":
        sign = -1
        opposite_sign = 1

    for _, call in calls.iterrows():
        if remaining_quantities[call.name] * sign <= 0:
            continue  # Skip if no remaining quantity for this leg

        # Look for a matching opposite call (different strike)
        for _, matching_call in calls.iterrows():
            if matching_call['strike'] <= call['strike'] or remaining_quantities[matching_call.name] * opposite_sign <= 0:
                continue  # Skip if matching call doesn't meet criteria

            # Look for matching puts for the opposite strike
            for _, matching_put_sell in puts.iterrows():
                if matching_put_sell['strike'] != call['strike'] or remaining_quantities[matching_put_sell.name] * opposite_sign <= 0:
                    continue  # Skip if put doesn't meet criteria

                # Look for matching puts for the first strike
                for _, matching_put_buy in puts.iterrows():
                    if matching_put_buy['strike'] != matching_call['strike'] or remaining_quantities[matching_put_buy.name] * sign <= 0:
                        continue  # Skip if put doesn't meet criteria

                    # Calculate box spread quantity as the minimum available quantity across the legs
                    box_quantity = min(
                        abs(remaining_quantities[call.name]),
                        abs(remaining_quantities[matching_call.name]),
                        abs(remaining_quantities[matching_put_sell.name]),
                        abs(remaining_quantities[matching_put_buy.name])
                    )

                    # Only add valid box spreads if the box quantity is positive
                    if box_quantity > 0:
                        print(f"Identified {spread_type} Box Spread - Quantity: {box_quantity} | Strikes: {call['strike']} - {matching_call['strike']} & {matching_put_sell['strike']} - {matching_put_buy['strike']}")
                        boxes.append({
                            'Client': client,
                            'Ticker': ticker,
                            'Maturity': maturity,
                            'Buy Call Strike': call['strike'] if spread_type == "Long" else matching_call['strike'],
                            'Sell Call Strike': matching_call['strike'] if spread_type == "Long" else call['strike'],
                            'Sell Put Strike': matching_put_sell['strike'] if spread_type == "Long" else matching_put_buy['strike'],
                            'Buy Put Strike': matching_put_buy['strike'] if spread_type == "Long" else matching_put_sell['strike'],
                            'Underlying Price': call['underlying_price'],
                            'Box Quantity': box_quantity,
                            'Spread Type': f'{spread_type} Box Spread'
                        })

                        # Deduct quantities for the legs used in the spread
                        remaining_quantities[call.name] -= box_quantity * sign
                        remaining_quantities[matching_call.name] += box_quantity * opposite_sign
                        remaining_quantities[matching_put_sell.name] += box_quantity * opposite_sign
                        remaining_quantities[matching_put_buy.name] -= box_quantity * sign


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
