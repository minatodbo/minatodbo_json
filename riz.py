df = df.sort_values(['stock', 'date']).reset_index(drop=True).copy()

# === Return and rolling volatility ===
df['return'] = df.groupby('stock')['price'].pct_change()
df['volatility'] = df.groupby('stock')['return'].transform(
    lambda x: x.rolling(rolling_window, min_periods=rolling_window//2).std()
)

# === Rolling median fee (smoother) ===
df['fee_med'] = df.groupby('stock')['fee'].transform(
    lambda x: x.rolling(rolling_window, min_periods=rolling_window // 2).median()
)

# === Spike detection ===
df['fee_jump'] = (df['fee'] > spike_multiplier * df['fee_med']).astype(int)

# === Count consecutive jump days ===
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

# === Initial base_pred (before retro billing or stress) ===
df['base_pred'] = np.where(
    df['jump_days'] >= min_persistence,
    blend_weight * df['fee_second'] + (1 - blend_weight) * df['fee'],
    df['fee_med']
)

# === Retro billing (only when jump_days == min_persistence) ===
for i in range(1, len(df)):
    if (
        df.loc[i, 'jump_days'] == min_persistence
        and df.loc[i, 'stock'] == df.loc[i - 1, 'stock']
    ):
        missed_diff = df.loc[i - 1, 'fee'] - df.loc[i - 1, 'fee_med']
        df.loc[i, 'base_pred'] += missed_diff

# === Z-score-based stress scaling ===
df['return_mean'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(rolling_window).mean())
df['return_std'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(rolling_window).std())
df['vol_mean'] = df.groupby('stock')['volatility'].transform(lambda x: x.rolling(rolling_window).mean())
df['vol_std'] = df.groupby('stock')['volatility'].transform(lambda x: x.rolling(rolling_window).std())

df['z_return'] = ((df['return'] - df['return_mean']) / df['return_std']).abs()
df['z_vol'] = ((df['volatility'] - df['vol_mean']) / df['vol_std']).clip(lower=0)

df['fee_stress_multiplier'] = 1 + (df['z_return'] * df['z_vol']) / 10  # scale as needed

# === Define stress condition ===
df['vol_diff'] = df['volatility'].diff()

stress_condition = (
    ((df['vol_diff'] > 0) & (df['return'] > 0.10)) |
    ((df['vol_diff'] > 0) & (df['return'] < 0)) |
    (df['return'] < -0.03)
)

# === Final fee prediction ===
df['fee_pred'] = df['base_pred'] * np.where(
    stress_condition,
    df['fee_stress_multiplier'],
    1.0
)
