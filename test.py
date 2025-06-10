import pandas as pd
import numpy as np

def smooth_fee_with_signals(df, 
                            rolling_window=20,
                            min_persistence=2,
                            spike_multiplier=2,
                            blend_weight=0.7,
                            adjustment_strength=0.2):
    """
    Parameters:
    - df: DataFrame with ['stock', 'date', 'fee', 'fee_second', 'price']
    - rolling_window: days used for smoothing and signals
    - min_persistence: days needed to confirm regime change
    - spike_multiplier: fee/median threshold for detecting spikes
    - blend_weight: blend ratio for persistent regime (fee vs fee_second)
    - adjustment_strength: how strongly signals shift fee_pred

    Returns:
    - df with new column 'fee_pred' (smoothed + adjusted fee)
    """

    df = df.sort_values(['stock', 'date']).copy()

    # === Rolling returns and vol ===
    df['return'] = df.groupby('stock')['price'].pct_change()
    df['volatility'] = df.groupby('stock')['return'].transform(
        lambda x: x.rolling(rolling_window, min_periods=rolling_window//2).std()
    )

    # Interaction signal: positive = bullish/stable, negative = bearish/volatile
    df['signal'] = df['return'] * df['volatility']

    # Rolling median of fee for baseline smoothing
    df['fee_med'] = df.groupby('stock')['fee'].transform(
        lambda x: x.rolling(rolling_window, min_periods=rolling_window//2).median()
    )

    # Spike detection: current fee significantly above recent history
    df['fee_jump'] = (df['fee'] > spike_multiplier * df['fee_med']).astype(int)

    # Count consecutive spike days
    def count_consecutive(arr):
        out = np.zeros_like(arr, dtype=int)
        c = 0
        for i, x in enumerate(arr):
            c = c + 1 if x else 0
            out[i] = c
            if not x:
                c = 0
        return out

    df['jump_days'] = df.groupby('stock')['fee_jump'].transform(
        lambda x: count_consecutive(x.values)
    )

    # Blend if regime change is persistent
    df['base_pred'] = np.where(
        df['jump_days'] >= min_persistence,
        blend_weight * df['fee_second'] + (1 - blend_weight) * df['fee'],
        df['fee_med']
    )

    # Apply signal-based adjustment
    # If signal < 0 (price down, vol up) → increase fee
    # If signal > 0 → reduce fee
    df['fee_pred'] = df['base_pred'] * (1 + adjustment_strength * -np.sign(df['signal'].fillna(0)))

    return df
