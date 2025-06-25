import pandas as pd
import numpy as np

def smooth_fee_with_signals(df, 
                            rolling_window=20,
                            min_persistence=2,
                            spike_multiplier=2,
                            blend_weight=0.7):
    """
    Smoothed and adjusted financing fee prediction model.

    Parameters:
    - df: DataFrame with ['stock', 'date', 'fee', 'fee_second', 'price']
    - rolling_window: size of rolling window for smoothing/stats
    - min_persistence: # of days to confirm spike regime
    - spike_multiplier: defines what is considered a "spike" vs median
    - blend_weight: weight given to fee_second vs fee when regime confirmed

    Returns:
    - df: same dataframe with 'fee_pred' (final predicted fee)
    """

    df = df.sort_values(['stock', 'date']).copy()

    # === Return and volatility ===
    df['return'] = df.groupby('stock')['price'].pct_change()
    df['volatility'] = df.groupby('stock')['return'].transform(
        lambda x: x.rolling(rolling_window, min_periods=rolling_window//2).std()
    )

    # === Rolling median smoothing ===
    df['fee_med'] = df.groupby('stock')['fee'].transform(
        lambda x: x.rolling(rolling_window, min_periods=rolling_window//2).median()
    )

    # === Spike detection and jump counter ===
    df['fee_jump'] = (df['fee'] > spike_multiplier * df['fee_med']).astype(int)

    def count_consecutive(arr):
        out = np.zeros_like(arr, dtype=int)
        c = 0
        for i, x in enumerate(arr):
            c = c + 1 if x else 0
            out[i] = c
            if not x:
                c = 0
        return out

    df['jump_days'] = df.groupby('stock')['fee_jump'].transform(lambda x: count_consecutive(x.values))

    # === Base smoothed rate before any adjustment ===
    df['base_pred'] = np.where(
        df['jump_days'] >= min_persistence,
        blend_weight * df['fee_second'] + (1 - blend_weight) * df['fee'],
        df['fee_med']
    )

    # === Retro-billing logic applied per stock ===
    def billing(d):
        d = d.reset_index(drop=True)
        for i in range(1, len(d)):
            if d.loc[i, 'jump_days'] == min_persistence:
                fee = d.loc[i - 1, 'fee']
                base = d.loc[i - 1, 'base_pred']
                miss = max(fee - base, 0)
                d.loc[i, 'base_pred'] += miss
        return d

    df = df.groupby('stock', group_keys=False).apply(billing).reset_index(drop=True)

    # === Stress signal (z-score logic) ===
    df['return_mean'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(rolling_window).mean())
    df['return_std'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(rolling_window).std())
    df['vol_mean'] = df.groupby('stock')['volatility'].transform(lambda x: x.rolling(rolling_window).mean())
    df['vol_std'] = df.groupby('stock')['volatility'].transform(lambda x: x.rolling(rolling_window).std())

    df['z_return'] = ((df['return'] - df['return_mean']) / df['return_std']).abs()
    df['z_vol'] = ((df['volatility'] - df['vol_mean']) / df['vol_std']).clip(lower=0)
    df['fee_stress_multiplier'] = 1 + (df['z_return'] * df['z_vol']) / 10  # can be tuned

    # === Stress condition logic ===
    df['vol_diff'] = df['volatility'].diff()

    stress_condition = (
        ((df['vol_diff'] > 0) & (df['return'] > 0.10)) |
        ((df['vol_diff'] > 0) & (df['return'] < 0)) |
        (df['return'] < -0.03)
    )

    # === Final prediction ===
    df['fee_pred'] = df['base_pred'] * np.where(
        stress_condition,
        df['fee_stress_multiplier'],
        1.0
    )

    return df
