import pandas as pd

def identify_spreads_with_strangles_and_risk_reversals(df):

    # Track used indices globally
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

    # Step 4: Identify Strangles
    strangles = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if call_row['quantity'] == 0 or i in used_indices:
            continue

        match = df[(df['option_type'] == 'Put') &
                   (df['maturity'] == call_row['maturity']) &
                   (df['quantity'] == call_row['quantity']) &
                   (df['strike'] != call_row['strike'])]
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
                       (df['strike'] < row['strike'])]
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
                       (df['strike'] > row['strike'])]
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

    # Step 6: Identify Iron Condor Spreads
    iron_condors = []

    for i, call_row in df[df['option_type'] == 'Call'].iterrows():
        if i in used_indices or call_row['quantity'] == 0:
            continue

        match1 = df[(df['option_type'] == 'Put') &
                    (df['maturity'] == call_row['maturity']) &
                    (df['strike'] == call_row['strike'])]
        if not match1.empty:
            match2 = df[(df['option_type'] == 'Call') &
                        (df['maturity'] == call_row['maturity']) &
                        (df['strike'] == call_row['strike'] + 10)]  # Strike + 10 for upper wing
            match3 = df[(df['option_type'] == 'Put') &
                        (df['maturity'] == call_row['maturity']) &
                        (df['strike'] == call_row['strike'] - 10)]  # Strike - 10 for lower wing

            if not match2.empty and not match3.empty:
                iron_condor_quantity = min(call_row['quantity'], match1.iloc[0]['quantity'],
                                           match2.iloc[0]['quantity'], match3.iloc[0]['quantity'])
                iron_condors.append({
                    'Client': call_row['client'],
                    'Ticker': call_row['ticker'],
                    'Maturity': call_row['maturity'],
                    'Sell Call Strike': call_row['strike'],
                    'Buy Call Strike': match2.iloc[0]['strike'],
                    'Sell Put Strike': match3.iloc[0]['strike'],
                    'Buy Put Strike': match1.iloc[0]['strike'],
                    'Underlying Price': call_row['underlying_price'],
                    'Iron Condor Quantity': iron_condor_quantity,
                    'Spread Type': 'Iron Condor'
                })
                used_indices.update([i, match1.index[0], match2.index[0], match3.index[0]])
                df.loc[i, 'quantity'] = 0
                df.loc[match1.index[0], 'quantity'] = 0
                df.loc[match2.index[0], 'quantity'] = 0
                df.loc[match3.index[0], 'quantity'] = 0

    iron_condor_df = pd.DataFrame(iron_condors)

    # Step 7: Identify Calendar Spreads
    calendar_spreads = []

    for i, row in df.iterrows():
        if i in used_indices or row['quantity'] == 0:
            continue

        if row['option_type'] == 'Call' and row['quantity'] > 0:
            match = df[(df['option_type'] == 'Call') &
                       (df['strike'] == row['strike']) &
                       (df['quantity'] < 0) &
                       (df['maturity'] > row['maturity'])]
            if not match.empty:
                calendar_quantity = min(row['quantity'], -match.iloc[0]['quantity'])
                calendar_spreads.append({
                    'Client': row['client'],
                    'Ticker': row['ticker'],
                    'Buy Call Maturity': row['maturity'],
                    'Sell Call Maturity': match.iloc[0]['maturity'],
                    'Strike': row['strike'],
                    'Underlying Price': row['underlying_price'],
                    'Calendar Quantity': calendar_quantity,
                    'Spread Type': 'Calendar Spread'
                })
                used_indices.update([i, match.index[0]])
                df.loc[i, 'quantity'] -= calendar_quantity
                df.loc[match.index[0], 'quantity'] += calendar_quantity

    calendar_spread_df = pd.DataFrame(calendar_spreads)

    # Return all identified spreads and strategies
    return straddle_df, synthetic_df, box_df, strangle_df, risk_reversal_df, iron_condor_df, calendar_spread_df
