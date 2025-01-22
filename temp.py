import pandas as pd
import pandas as pd

def identify_spreads_with_strangles_and_risk_reversals(df):

    # Track used indices globally
    used_indices = set()

    # Step 1: Identify Straddles
    straddles = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if i in used_indices:
            continue

        # Ensure that the ticker is the same for matching options
        match = df[(df['option_type'] == 'Put') &
                   (df['strike'] == call_row['strike']) &
                   (df['maturity'] == call_row['maturity']) &
                   (df['quantity'] == call_row['quantity']) &
                   (df['client'] == call_row['client']) & (df['ticker'] == call_row['ticker'])]  # Ticker check added

        if not match.empty:
            straddle_quantity = call_row['quantity']
            straddle_type = "Long Straddle" if straddle_quantity > 0 else "Short Straddle"

            if straddle_type == "Short Straddle":
                straddles.append({
                    'Client': call_row['client'],
                    'Ticker': call_row['ticker'],
                    'Maturity': call_row['maturity'],
                    'Buy Call Strike': None,
                    'Sell Call Strike': call_row['strike'],
                    'Buy Put Strike': None,
                    'Sell Put Strike': call_row['strike'],
                    'Underlying Price': call_row['underlying_price'],
                    'Straddle Quantity': abs(straddle_quantity),
                    'Spread Type': straddle_type
                })
            else:
                straddles.append({
                    'Client': call_row['client'],
                    'Ticker': call_row['ticker'],
                    'Maturity': call_row['maturity'],
                    'Buy Call Strike': call_row['strike'],
                    'Sell Call Strike': None,
                    'Buy Put Strike': call_row['strike'],
                    'Sell Put Strike': None,
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

    # Step 2a: Match Synthetic Positions with Equal Quantities
    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            matches = df[(df['option_type'] == 'Put') &
                         (df['strike'] == row['strike']) &
                         (df['maturity'] == row['maturity']) &
                         (df['quantity'] == -row['quantity']) &
                         (df['client'] == row['client']) &
                         (df['ticker'] == row['ticker'])]

            for j, match in matches.iterrows():
                synthetic_quantity = row['quantity']

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

                used_indices.update([i, j])
                df.loc[i, 'quantity'] = 0
                df.loc[j, 'quantity'] = 0

        elif row['option_type'] == 'Put' and row['quantity'] > 0:
            matches = df[(df['option_type'] == 'Call') &
                         (df['strike'] == row['strike']) &
                         (df['maturity'] == row['maturity']) &
                         (df['quantity'] == -row['quantity']) &
                         (df['client'] == row['client']) &
                         (df['ticker'] == row['ticker'])]

            for j, match in matches.iterrows():
                synthetic_quantity = row['quantity']

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

                used_indices.update([i, j])
                df.loc[i, 'quantity'] = 0
                df.loc[j, 'quantity'] = 0

    # Step 2b: Match Synthetic Positions with Different Quantities
    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            matches = df[(df['option_type'] == 'Put') &
                         (df['strike'] == row['strike']) &
                         (df['maturity'] == row['maturity']) &
                         (df['quantity'] < 0) &
                         (df['client'] == row['client']) &
                         (df['ticker'] == row['ticker'])]

            for j, match in matches.iterrows():
                synthetic_quantity = min(row['quantity'], -match['quantity'])

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

                df.loc[i, 'quantity'] -= synthetic_quantity
                df.loc[j, 'quantity'] += synthetic_quantity

                if df.loc[i, 'quantity'] == 0:
                    used_indices.add(i)
                if df.loc[j, 'quantity'] == 0:
                    used_indices.add(j)

        elif row['option_type'] == 'Put' and row['quantity'] > 0:
            matches = df[(df['option_type'] == 'Call') &
                         (df['strike'] == row['strike']) &
                         (df['maturity'] == row['maturity']) &
                         (df['quantity'] < 0) &
                         (df['client'] == row['client']) &
                         (df['ticker'] == row['ticker'])]

            for j, match in matches.iterrows():
                synthetic_quantity = min(row['quantity'], -match['quantity'])

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

                df.loc[i, 'quantity'] -= synthetic_quantity
                df.loc[j, 'quantity'] += synthetic_quantity

                if df.loc[i, 'quantity'] == 0:
                    used_indices.add(i)
                if df.loc[j, 'quantity'] == 0:
                    used_indices.add(j)

    synthetic_df = pd.DataFrame(synthetics)

    # Step 3: Identify Box Spreads
    boxes = []
    used_synthetics = set()

    if not synthetic_df.empty:
        synthetic_df = synthetic_df[synthetic_df['Synthetic Quantity'] > 0]

        # Step 3a: Match Synthetics with Equal Quantities
        for i, long_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Long'].iterrows():
            for j, short_row in synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Short'].iterrows():
                if i in used_synthetics or j in used_synthetics:
                    continue

                if (long_row['Client'] == short_row['Client'] and
                        long_row['Ticker'] == short_row['Ticker'] and
                        long_row['Maturity'] == short_row['Maturity'] and
                        long_row['Synthetic Quantity'] == short_row['Synthetic Quantity']):
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
                        'Spread Type': 'Short Box Spread' if long_row['Buy Call Strike'] > short_row[
                            'Buy Put Strike'] else 'Long Box Spread'
                    })

                    used_synthetics.update([i, j])
                    synthetic_df = synthetic_df.drop([i, j])
                    break

        # Step 3b: Match Synthetics with Different Quantities
        while True:
            long_synthetics = synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Long']
            short_synthetics = synthetic_df[synthetic_df['Spread Type'] == 'Synthetic Short']

            if long_synthetics.empty or short_synthetics.empty:
                break

            best_pair = None
            max_cash_diff = float('-inf')

            for i, long_row in long_synthetics.iterrows():
                for j, short_row in short_synthetics.iterrows():
                    if i in used_synthetics or j in used_synthetics:
                        continue

                    if (long_row['Client'] == short_row['Client'] and
                            long_row['Ticker'] == short_row['Ticker'] and
                            long_row['Maturity'] == short_row['Maturity'] and
                            long_row['Buy Call Strike'] != short_row['Buy Put Strike']):

                        quantity = min(long_row['Synthetic Quantity'], short_row['Synthetic Quantity'])
                        cash_diff = quantity * abs(long_row['Buy Call Strike'] - short_row['Buy Put Strike'])

                        if cash_diff > max_cash_diff:
                            max_cash_diff = cash_diff
                            best_pair = (i, j, quantity)

            if best_pair is None:
                break

            i, j, quantity = best_pair
            long_row = synthetic_df.loc[i]
            short_row = synthetic_df.loc[j]

            boxes.append({
                'Client': long_row['Client'],
                'Ticker': long_row['Ticker'],
                'Maturity': long_row['Maturity'],
                'Buy Call Strike': long_row['Buy Call Strike'],
                'Sell Call Strike': short_row['Sell Call Strike'],
                'Buy Put Strike': short_row['Buy Put Strike'],
                'Sell Put Strike': long_row['Sell Put Strike'],
                'Underlying Price': long_row['Underlying Price'],
                'Box Quantity': quantity,
                'Spread Type': 'Short Box Spread' if long_row['Buy Call Strike'] > short_row[
                    'Buy Put Strike'] else 'Long Box Spread'
            })

            synthetic_df.loc[i, 'Synthetic Quantity'] -= quantity
            synthetic_df.loc[j, 'Synthetic Quantity'] -= quantity

            if synthetic_df.loc[i, 'Synthetic Quantity'] == 0:
                used_synthetics.add(i)
            if synthetic_df.loc[j, 'Synthetic Quantity'] == 0:
                used_synthetics.add(j)

    box_df = pd.DataFrame(boxes)

    # Step 4: Identify Strangles
    strangles = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if call_row['quantity'] == 0 or i in used_indices:
            continue

        # Match Call with Put at the same maturity and quantity, but different strikes
        match = df[(df['option_type'] == 'Put') &
                   (df['maturity'] == call_row['maturity']) &
                   (df['quantity'] == call_row['quantity']) &
                   (df['strike'] != call_row['strike']) &
                   (df['client'] == call_row['client']) & (df['ticker'] == call_row['ticker'])]  # Ticker check added
        if not match.empty:
            strangle_quantity = call_row['quantity']
            if strangle_quantity > 0:
                strangles.append({
                    'Client': call_row['client'],
                    'Ticker': call_row['ticker'],
                    'Maturity': call_row['maturity'],
                    'Buy Call Strike': call_row['strike'],
                    'Buy Put Strike': match.iloc[0]['strike'],
                    'Underlying Price': call_row['underlying_price'],
                    'Strangle Quantity': abs(strangle_quantity),
                    'Spread Type': 'Long Strangle'
                })
            else:
                strangles.append({
                    'Client': call_row['client'],
                    'Ticker': call_row['ticker'],
                    'Maturity': call_row['maturity'],
                    'Sell Call Strike': call_row['strike'],
                    'Sell Put Strike': match.iloc[0]['strike'],
                    'Underlying Price': call_row['underlying_price'],
                    'Strangle Quantity': abs(strangle_quantity),
                    'Spread Type': 'Short Strangle'
                })
            used_indices.update([i, match.index[0]])
            df.loc[i, 'quantity'] = 0
            df.loc[match.index[0], 'quantity'] = 0

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
df = pd.read_excel(r'C:\Users\karim\Downloads\pf3.xlsx')

data = {
    'client': ['ClientA'] * 2,
    'ticker': ['ABC'] * 2,
    'underlying_price': [100] * 2,
    'quantity': [-6, 10],
    'strike': [1000, 2000],
    'option_type': ['Put', 'Put'],
    'maturity': ['2024/12/31'] * 2,
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
call_spread_df.to_clipboard()
