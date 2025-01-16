import pandas as pd

def identify_spreads_with_strangles_and_risk_reversals(df):

    # Track used indices globally
    used_indices = set()
    # Step 1: Identify Straddles (with proper quantity handling)
    straddles = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if call_row['quantity'] == 0 or i in used_indices:
            continue

        # Match Call with Put at the same strike, maturity, client, and ticker
        match = df[(df['option_type'] == 'Put') &
                   (df['strike'] == call_row['strike']) &
                   (df['maturity'] == call_row['maturity']) &
                   (df['client'] == call_row['client']) &
                   (df['ticker'] == call_row['ticker']) &
                   (~df.index.isin(used_indices))]

        if not match.empty:
            for j, put_row in match.iterrows():
                # Determine the straddle quantity (minimum of Call and Put quantities)
                straddle_quantity = min(call_row['quantity'], put_row['quantity'])

                if straddle_quantity > 0:
                    straddle_type = "Long Straddle" if call_row['quantity'] > 0 else "Short Straddle"

                    straddles.append({
                        'Client': call_row['client'],
                        'Ticker': call_row['ticker'],
                        'Maturity': call_row['maturity'],
                        'Buy Call Strike': call_row['strike'] if straddle_type == "Long Straddle" else None,
                        'Sell Call Strike': None if straddle_type == "Long Straddle" else call_row['strike'],
                        'Buy Put Strike': put_row['strike'] if straddle_type == "Long Straddle" else None,
                        'Sell Put Strike': None if straddle_type == "Long Straddle" else put_row['strike'],
                        'Underlying Price': call_row['underlying_price'],
                        'Straddle Quantity': straddle_quantity,
                        'Spread Type': straddle_type
                    })

                    # Update quantities
                    df.loc[i, 'quantity'] -= straddle_quantity
                    df.loc[j, 'quantity'] -= straddle_quantity

                    # Add used indices to the tracker
                    if df.loc[i, 'quantity'] == 0:
                        used_indices.add(i)
                    if df.loc[j, 'quantity'] == 0:
                        used_indices.add(j)

                    # Break after processing this match
                    break

    straddle_df = pd.DataFrame(straddles)

    # Step 2: Identify Synthetic Positions
    synthetics = []

    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            # Match Buy Call with Sell Put at the same strike, maturity, and ticker
            match = df[(df['option_type'] == 'Put') &
                       (df['strike'] == row['strike']) &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0) &
                       (df['client'] == row['client']) & (df['ticker'] == row['ticker'])]  # Ticker check added
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
            # Match Buy Put with Sell Call at the same strike, maturity, and ticker
            match = df[(df['option_type'] == 'Call') &
                       (df['strike'] == row['strike']) &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0) &
                       (df['client'] == row['client']) & (df['ticker'] == row['ticker'])]  # Ticker check added
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

    # Step 3: Identify Box Spreads (fixed for cases with no synthetics and handling different quantities)
    boxes = []
    used_synthetics = set()

    if not synthetic_df.empty and 'Synthetic Quantity' in synthetic_df.columns:
        # Filter out rows where Synthetic Quantity is zero or negative
        synthetic_df = synthetic_df[synthetic_df['Synthetic Quantity'] > 0]

        for i, long_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Long'].iterrows():
            for j, short_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Short'].iterrows():
                if i in used_synthetics or j in used_synthetics:
                    continue

                # Ensure the ticker and client are the same for both long and short positions
                if (long_row['Maturity'] == short_row['Maturity'] and
                        long_row['Ticker'] == short_row['Ticker'] and
                        long_row['Client'] == short_row['Client'] and
                        long_row['Buy Call Strike'] != short_row['Buy Put Strike']):

                    # Determine the box spread quantity (minimum of the two synthetic quantities)
                    box_quantity = min(long_row['Synthetic Quantity'], short_row['Synthetic Quantity'])

                    # Append the box spread
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
                        'Spread Type': 'Short Box Spread' if long_row['Buy Call Strike'] > short_row[
                            'Buy Put Strike'] else 'Long Box Spread'
                    })

                    # Update the remaining synthetic quantities
                    synthetic_df.loc[i, 'Synthetic Quantity'] -= box_quantity
                    synthetic_df.loc[j, 'Synthetic Quantity'] -= box_quantity

                    # Mark synthetic positions as used if their quantities are fully consumed
                    if synthetic_df.loc[i, 'Synthetic Quantity'] == 0:
                        used_synthetics.add(i)
                    if synthetic_df.loc[j, 'Synthetic Quantity'] == 0:
                        used_synthetics.add(j)

    # Create the box spread DataFrame
    box_df = pd.DataFrame(boxes)

    # Step 4: Identify Strangles (with proper quantity handling)
    strangles = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if call_row['quantity'] == 0 or i in used_indices:
            continue

        # Match Call with Put at the same maturity, client, and ticker, but different strikes
        match = df[(df['option_type'] == 'Put') &
                   (df['maturity'] == call_row['maturity']) &
                   (df['client'] == call_row['client']) &
                   (df['ticker'] == call_row['ticker']) &
                   (df['strike'] != call_row['strike']) &
                   (~df.index.isin(used_indices))]

        if not match.empty:
            for j, put_row in match.iterrows():
                # Determine the strangle quantity (minimum of Call and Put quantities)
                strangle_quantity = min(call_row['quantity'], put_row['quantity'])

                if strangle_quantity > 0:
                    spread_type = "Long Strangle" if call_row['quantity'] > 0 else "Short Strangle"

                    strangles.append({
                        'Client': call_row['client'],
                        'Ticker': call_row['ticker'],
                        'Maturity': call_row['maturity'],
                        'Buy Call Strike': call_row['strike'] if spread_type == "Long Strangle" else None,
                        'Sell Call Strike': None if spread_type == "Long Strangle" else call_row['strike'],
                        'Buy Put Strike': put_row['strike'] if spread_type == "Long Strangle" else None,
                        'Sell Put Strike': None if spread_type == "Long Strangle" else put_row['strike'],
                        'Underlying Price': call_row['underlying_price'],
                        'Strangle Quantity': strangle_quantity,
                        'Spread Type': spread_type
                    })

                    # Update quantities
                    df.loc[i, 'quantity'] -= strangle_quantity
                    df.loc[j, 'quantity'] -= strangle_quantity

                    # Mark indices as used if their quantities are fully consumed
                    if df.loc[i, 'quantity'] == 0:
                        used_indices.add(i)
                    if df.loc[j, 'quantity'] == 0:
                        used_indices.add(j)

                    break  # Only match with the first available Put
    strangle_df = pd.DataFrame(strangles)

    # Step 5: Identify Risk Reversals
    risk_reversals = []

    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            match = df[(df['option_type'] == 'Put') &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0) &
                       (df['strike'] < row['strike']) &
                       (df['client'] == row['client']) & (df['ticker'] == row['ticker'])]  # Ticker check added
            if not match.empty:
                reversal_quantity = min(row['quantity'], -match.iloc[0]['quantity'])
                risk_reversals.append({
                    'Client': row['client'],
                    'Ticker': row['ticker'],
                    'Maturity': row['maturity'],
                    'Buy Call Strike': row['strike'],
                    'Sell Put Strike': match.iloc[0]['strike'],
                    'Underlying Price': row['underlying_price'],
                    'Reversal Quantity': reversal_quantity,
                    'Spread Type': 'Long Risk Reversal'
                })
                used_indices.update([i, match.index[0]])
                df.loc[i, 'quantity'] -= reversal_quantity
                df.loc[match.index[0], 'quantity'] += reversal_quantity

        elif row['option_type'] == 'Put' and row['quantity'] > 0:
            match = df[(df['option_type'] == 'Call') &
                       (df['maturity'] == row['maturity']) &
                       (df['quantity'] < 0) &
                       (df['strike'] > row['strike']) &
                       (df['client'] == row['client']) & (df['ticker'] == row['ticker'])]  # Ticker check added
            if not match.empty:
                reversal_quantity = min(row['quantity'], -match.iloc[0]['quantity'])
                risk_reversals.append({
                    'Client': row['client'],
                    'Ticker': row['ticker'],
                    'Maturity': row['maturity'],
                    'Buy Put Strike': row['strike'],
                    'Sell Call Strike': match.iloc[0]['strike'],
                    'Underlying Price': row['underlying_price'],
                    'Reversal Quantity': reversal_quantity,
                    'Spread Type': 'Short Risk Reversal'
                })
                used_indices.update([i, match.index[0]])
                df.loc[i, 'quantity'] -= reversal_quantity
                df.loc[match.index[0], 'quantity'] += reversal_quantity

    risk_reversal_df = pd.DataFrame(risk_reversals)

    # Step 6: Identify Call Spreads
    call_spreads = []
    used_indices = set()  # Track used indices to avoid double-counting

    for i, buy_call in df[(df['option_type'] == 'Call') & (df['quantity'] > 0)].iterrows():
        if i in used_indices:  # Skip if already part of a spread
            continue

        # Match with a sell call (same maturity, different strikes, same ticker)
        matches = df[(df['option_type'] == 'Call') &
                     (df['quantity'] < 0) &
                     (df['maturity'] == buy_call['maturity']) &
                     (df['strike'] != buy_call['strike']) &
                     (df['client'] == buy_call['client']) & (df['ticker'] == buy_call['ticker']) &  # Ticker check added
                     (~df.index.isin(used_indices))]

        if not matches.empty:
            # Take the first matching sell call
            for j, sell_call in matches.iterrows():
                # Determine the spread quantity
                spread_quantity = min(buy_call['quantity'], -sell_call['quantity'])

                # Define spread type
                spread_type = "Debit Call Spread" if buy_call['strike'] < sell_call['strike'] else "Credit Call Spread"

                call_spreads.append({
                    'Client': buy_call['client'],
                    'Ticker': buy_call['ticker'],
                    'Maturity': buy_call['maturity'],
                    'Buy Call Strike': buy_call['strike'],
                    'Sell Call Strike': sell_call['strike'],
                    'Underlying Price': buy_call['underlying_price'],
                    'Call Spread Quantity': spread_quantity,
                    'Spread Type': spread_type
                })

                # Update quantities
                df.loc[i, 'quantity'] -= spread_quantity
                df.loc[j, 'quantity'] += spread_quantity

                # Mark indices as used
                used_indices.update([i, j])

                # Break after first match to ensure no double-counting
                break

    call_spread_df = pd.DataFrame(call_spreads)

    # Step 7: Identify Put Spreads
    put_spreads = []

    for i, buy_put in df[(df['option_type'] == 'Put') & (df['quantity'] > 0)].iterrows():
        if i in used_indices:  # Skip if already part of a spread
            continue

        # Match with a sell put (same maturity, different strikes, same ticker)
        matches = df[(df['option_type'] == 'Put') &
                     (df['quantity'] < 0) &
                     (df['maturity'] == buy_put['maturity']) &
                     (df['strike'] != buy_put['strike']) &
                     (df['client'] == buy_put['client']) & (df['ticker'] == buy_put['ticker']) &  # Ticker check added
                     (~df.index.isin(used_indices))]

        if not matches.empty:
            for j, sell_put in matches.iterrows():
                # Determine the spread quantity
                spread_quantity = min(buy_put['quantity'], -sell_put['quantity'])

                # Define spread type
                spread_type = "Bull Put Spread" if buy_put['strike'] < sell_put['strike'] else "Bear Put Spread"

                put_spreads.append({
                    'Client': buy_put['client'],
                    'Ticker': buy_put['ticker'],
                    'Maturity': buy_put['maturity'],
                    'Buy Put Strike': buy_put['strike'],
                    'Sell Put Strike': sell_put['strike'],
                    'Underlying Price': buy_put['underlying_price'],
                    'Put Spread Quantity': spread_quantity,
                    'Spread Type': spread_type
                })

                # Update quantities
                df.loc[i, 'quantity'] -= spread_quantity
                df.loc[j, 'quantity'] += spread_quantity

                # Mark indices as used
                used_indices.update([i, j])

                # Break to avoid double-counting
                break

    put_spread_df = pd.DataFrame(put_spreads)

    return straddle_df, synthetic_df, box_df, strangle_df, risk_reversal_df ,call_spread_df , put_spread_df

# Example DataFrame (replace this with your actual data)
data = {
    'client': ['ClientA'] * 4,
    'ticker': ['ABC'] * 4,
    'underlying_price': [100] * 4,
    'quantity': [-6, 6, 9, -5],
    'strike': [1000, 2000,1000,2000],
    'option_type': ['Call', 'Call', 'Put', 'Put'],
    'maturity': ['2024/12/31'] * 4,
}
df = pd.DataFrame(data)
# Identify strategies
straddle_df, synthetic_df, box_df, strangle_df, risk_reversal_df , call_spread_df , put_spread_df= identify_spreads_with_strangles_and_risk_reversals(df)
pd.set_option('display.max_columns', 10)
# Output the results
print("Straddle Spread:")
print(straddle_df)

print("\nSynthetic Positions:")
print(synthetic_df)

print("\nBox Spread:")
print(box_df)

print("\nStrangle Spread:")
print(strangle_df)

print("\nRisk Spread:")
print(risk_reversal_df)

print("\nCall Spread:")
print(call_spread_df)

print("\nPut Spread:")
print(put_spread_df)

print(df)
