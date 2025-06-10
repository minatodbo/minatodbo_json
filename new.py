import pandas as pd
import numpy as np

def smooth_fee_with_regime_logic(df,
                                  rolling_window=20,
                                  min_persistence=2,
                                  z_threshold=2,
                                  blend_weight=0.7,
                                  alpha=0.05,
                                  beta=0.1,
                                  gamma=0.1):
    """
    Enhanced spike-resistant fee smoother with regime detection and volatility/return adjustment.

    Parameters:
    - df: DataFrame with ['stock', 'date', 'price', 'fee', 'fee_second']
    - rolling_window: for smoothing and z-score calculation
    - min_persistence: how many days spike must persist to accept regime change
    - z_threshold: threshold for spike detection (z-score)
    - blend_weight: weight for blending fee_second when regime changes
    - alpha, beta, gamma: weights for return, volatility, and interaction term

    Returns:
    - df with added 'fee_pred' column (smoothed fee)
    """

    df = df.sort_values(['stock', 'date']).copy()

    # Compute log return and rolling volatility on price
    df['return'] = df.groupby('stock')['price'].transform(lambda x: np.log(x).diff())
    df['volatility'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(rolling_window, min_periods=5).std())
    df['interaction'] = df['return'] * df['volatility']

    # Rolling stats on fee
    df['fee_mean'] = df.groupby('stock')['fee'].transform(lambda x: x.rolling(rolling_window, min_periods=5).mean())
    df['fee_std'] = df.groupby('stock')['fee'].transform(lambda x: x.rolling(rolling_window, min_periods=5).std())
    df['fee_z'] = (df['fee'] - df['fee_mean']) / df['fee_std']

    # Spike detection using z-score
    df['fee_jump'] = (df['fee_z'] > z_threshold).astype(int)

    # Count consecutive jump days
    def count_consecutive(arr):
        out = np.zeros_like(arr, dtype=int)
        count = 0
        for i, val in enumerate(arr):
            if val:
                count += 1
            else:
                count = 0
            out[i] = count
        return out

    df['jump_days'] = df.groupby('stock')['fee_jump'].transform(lambda x: count_consecutive(x.values))

    # Base prediction: rolling mean
    df['base_pred'] = df['fee_mean']

    # When regime confirmed, retroactively adjust previous day's pred
    df['adjusted_fee'] = np.where(
        df['jump_days'] >= min_persistence,
        blend_weight * df['fee_second'] + (1 - blend_weight) * df['fee'],
        df['base_pred']
    )

    # Retroactive fix: if regime confirmed on day t, fix day t-1
    df['fee_pred'] = df['adjusted_fee']
    for i in range(1, len(df)):
        if df.iloc[i]['jump_days'] == min_persistence:
            df.iloc[i - 1, df.columns.get_loc('fee_pred')] = df.iloc[i]['adjusted_fee']

    # Vol/Return Adjustment
    adj = alpha * df['return'].fillna(0) + beta * df['volatility'].fillna(0) + gamma * df['interaction'].fillna(0)
    df['fee_pred'] = df['fee_pred'] * (1 + adj)

    return df
