def find_box_spreads(df):
    """
    Identify box spreads in the given options portfolio DataFrame.
    
    A box spread combines:
    - A bull call spread (buy call at lower strike, sell call at higher strike)
    - A bear put spread (sell put at lower strike, buy put at higher strike)

    Args:
        df (pd.DataFrame): Options portfolio with columns:
            - underlying type, underlying price, quantity, strike, side, 
              option type (C or P), maturity, ticker, client.

    Returns:
        pd.DataFrame: DataFrame with identified box spreads and their details.
    """
    box_spreads = []

    # Group by client and underlying type
    for client, client_data in df.groupby("client"):  # Assuming 'client' column exists
        for underlying, group in client_data.groupby("underlying type"):
            # Separate calls and puts
            calls = group[group["option type"] == "C"]
            puts = group[group["option type"] == "P"]

            # Iterate over combinations of two strikes for calls and puts
            for _, call_low in calls.iterrows():
                for _, call_high in calls.iterrows():
                    if call_low["strike"] >= call_high["strike"]:
                        continue

                    for _, put_low in puts.iterrows():
                        for _, put_high in puts.iterrows():
                            if put_low["strike"] >= put_high["strike"]:
                                continue

                            # Check for box spread conditions
                            if (
                                call_low["strike"] == put_low["strike"]  # Match lower strikes
                                and call_high["strike"] == put_high["strike"]  # Match higher strikes
                                and call_low["side"] == "B"  # Buy lower strike call
                                and call_high["side"] == "S"  # Sell higher strike call
                                and put_low["side"] == "S"  # Sell lower strike put
                                and put_high["side"] == "B"  # Buy higher strike put
                            ):
                                # Long box spread
                                box_spreads.append({
                                    "client": client,
                                    "underlying type": underlying,
                                    "box_type": "long",
                                    "lower_strike": call_low["strike"],
                                    "higher_strike": call_high["strike"],
                                    "quantity": min(
                                        abs(call_low["quantity"]),
                                        abs(call_high["quantity"]),
                                        abs(put_low["quantity"]),
                                        abs(put_high["quantity"])
                                    )
                                })

                            elif (
                                call_low["strike"] == put_low["strike"]  # Match lower strikes
                                and call_high["strike"] == put_high["strike"]  # Match higher strikes
                                and call_low["side"] == "S"  # Sell lower strike call
                                and call_high["side"] == "B"  # Buy higher strike call
                                and put_low["side"] == "B"  # Buy lower strike put
                                and put_high["side"] == "S"  # Sell higher strike put
                            ):
                                # Short box spread
                                box_spreads.append({
                                    "client": client,
                                    "underlying type": underlying,
                                    "box_type": "short",
                                    "lower_strike": call_low["strike"],
                                    "higher_strike": call_high["strike"],
                                    "quantity": min(
                                        abs(call_low["quantity"]),
                                        abs(call_high["quantity"]),
                                        abs(put_low["quantity"]),
                                        abs(put_high["quantity"])
                                    )
                                })

    # Convert the results into a DataFrame
    return pd.DataFrame(box_spreads)
