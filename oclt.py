import pandas as pd

def identify_all_strategies(df):
    # Track used indices globally to avoid double-counting
    used_indices = set()

    # Step 1: Identify Straddles
    straddles = []
    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if i in used_indices:
            continue

        # Match Call with Put at the same strike, maturity, and quantity
        match = df[(df['option_type'] == 'Put') &
                   (df['strike'] == call_row['strike']) &
                   (df['maturity'] == call_row['maturity']) &
                   (df['quantity'] == call_row['quantity'])]

        if not match.empty:
            straddle_quantity = call_row['quantity']
            straddle_type = "Long Straddle" if straddle_quantity > 0 else "Short Straddle"

            straddles.append({
                'Client': call_row['client'],
                'Ticker': call_row['ticker'],
                'Maturity': call_row['maturity'],
                'Buy Call Strike': call_row['strike'] if straddle_type == "Long Straddle" else None,
                'Sell Call Strike': call_row['strike'] if straddle_type == "Short Straddle" else None,
                'Buy Put Strike': call_row['strike'] if straddle_type == "Long Straddle" else None,
                'Sell Put Strike': call_row['strike'] if straddle_type == "Short Straddle" else None,
                'Underlying Price': call_row['underlying_price'],
                'Straddle Quantity': abs(straddle_quantity),
                'Spread Type': straddle_type
            })

            used_indices.update([i, match.index[0]])
            df.loc[i, 'quantity'] = 0
            df.loc[match.index[0], 'quantity'] = 0

    straddle_df = pd.DataFrame(straddles)

    # Step 2: Identify Synthetic Positions
    synthetics = []
    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            # Match Buy Call with Sell Put at the same strike and maturity
            match = df[(df['option_type'] == 'Put') &
                       (df['strike'] == row['strike']) &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0)]
            if not match.empty:
                synthetic_quantity = min(row['quantity'], -match.iloc[0]['quantity'])
                synthetics.append({
                    'Client': row['client'],
                    'Ticker': row['ticker'],
                    'Maturity': row['maturity'],
                    'Buy Call Strike': row['strike'],
                    'Sell Put Strike': row['strike'],
                    'Underlying Price': row['underlying_price'],
                    'Synthetic Quantity': synthetic_quantity,
                    'Spread Type': 'Synthetic Long'
                })
                used_indices.update([i, match.index[0]])
                df.loc[i, 'quantity'] -= synthetic_quantity
                df.loc[match.index[0], 'quantity'] += synthetic_quantity

        elif row['option_type'] == 'Put' and row['quantity'] > 0:
            # Match Buy Put with Sell Call at the same strike and maturity
            match = df[(df['option_type'] == 'Call') &
                       (df['strike'] == row['strike']) &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0)]
            if not match.empty:
                synthetic_quantity = min(row['quantity'], -match.iloc[0]['quantity'])
                synthetics.append({
                    'Client': row['client'],
                    'Ticker': row['ticker'],
                    'Maturity': row['maturity'],
                    'Buy Put Strike': row['strike'],
                    'Sell Call Strike': row['strike'],
                    'Underlying Price': row['underlying_price'],
                    'Synthetic Quantity': synthetic_quantity,
                    'Spread Type': 'Synthetic Short'
                })
                used_indices.update([i, match.index[0]])
                df.loc[i, 'quantity'] -= synthetic_quantity
                df.loc[match.index[0], 'quantity'] += synthetic_quantity

    synthetic_df = pd.DataFrame(synthetics)

    # Step 3: Identify Box Spreads
    boxes = []
    used_synthetics = set()
    for i, long_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Long'].iterrows():
        for j, short_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Short'].iterrows():
            if i in used_synthetics or j in used_synthetics:
                continue
            if (long_row['Maturity'] == short_row['Maturity'] and
                    long_row['Synthetic Quantity'] == short_row['Synthetic Quantity'] and
                    long_row['Buy Call Strike'] != short_row['Buy Put Strike']):
                box_quantity = long_row['Synthetic Quantity']
                boxes.append({
                    'Client': long_row['Client'],
                    'Ticker': long_row['Ticker'],
                    'Maturity': long_row['Maturity'],
                    'Buy Call Strike': long_row['Buy Call Strike'],
                    'Sell Call Strike': short_row['Sell Call Strike'],
                    'Buy Put Strike': short_row['Buy Put Strike'],
                    'Sell Put Strike': long_row['Sell Put Strike'],
                    'Underlying Price': long_row['Underlying Price'],
                    'Box Quantity': box_quantity,
                    'Spread Type': 'Short Box Spread' if long_row['Buy Call Strike'] > short_row['Buy Put Strike'] else 'Long Box Spread'
                })
                used_synthetics.update([i, j])
                synthetic_df = synthetic_df.drop([i, j])
                break

    box_df = pd.DataFrame(boxes)

    # Additional strategy steps go here (Strangles, Risk Reversals, Call Spreads, Put Spreads)
    # Repeat similar logic, preserving indices and ensuring client and ticker details

    return straddle_df, synthetic_df, box_df

# Example usage
# df = pd.DataFrame(...)  # Provide the actual DataFrame
straddle_df, synthetic_df, box_df = identify_all_strategies(df)

# Output the results
print("Straddle Spread:")
print(straddle_df)

print("\nSynthetic Positions:")
print(synthetic_df)

print("\nBox Spread:")
print(box_df)
