import numpy as np

def fx_swap_npv_dual(spot_rate, forward_rate, notional_usd, usd_rate, eur_rate, tenor):
    """
    Compute NPV of an FX Swap from both USD and EUR perspectives.
    
    Parameters:
    - spot_rate (float): Spot FX rate (EUR/USD).
    - forward_rate (float): Forward FX rate at maturity.
    - notional_usd (float): Notional amount in USD.
    - usd_rate (float): USD interest rate (annualized).
    - eur_rate (float): EUR interest rate (annualized).
    - tenor (float): Remaining tenor of the FX swap in days.
    
    Returns:
    - npv_usd (float): NPV of the FX swap in USD terms.
    - npv_eur (float): NPV of the FX swap in EUR terms.
    """
    # Convert rates to decimals
    usd_rate = usd_rate / 100
    eur_rate = eur_rate / 100
    
    # Compute the discount factors
    days_in_year = 360  # Market convention
    discount_usd = 1 / (1 + usd_rate * tenor / days_in_year)
    discount_eur = 1 / (1 + eur_rate * tenor / days_in_year)
    
    # Compute cashflows
    notional_eur = notional_usd / spot_rate  # Notional amount in EUR
    usd_forward_cashflow = notional_usd  # USD cashflow at forward date
    eur_forward_cashflow = notional_eur * forward_rate  # EUR cashflow at forward rate

    # Present value of cashflows
    pv_usd_cashflow = usd_forward_cashflow * discount_usd
    pv_eur_cashflow = eur_forward_cashflow * discount_eur

    # NPV from USD perspective
    npv_usd = pv_usd_cashflow - (pv_eur_cashflow / spot_rate)
    
    # NPV from EUR perspective
    npv_eur = (pv_usd_cashflow * spot_rate) - pv_eur_cashflow

    return npv_usd, npv_eur

# Example inputs
spot_rate = 1.0509          # Spot EUR/USD
forward_rate = 1.0548       # Forward EUR/USD
notional_usd = 100_000_000  # USD 100 million
usd_rate = 4.59             # USD interest rate (annualized in %)
eur_rate = 3.15             # EUR interest rate (annualized in %)
tenor = 30                  # Remaining tenor in days (e.g., 30 days)

# Compute NPV
npv_usd, npv_eur = fx_swap_npv_dual(spot_rate, forward_rate, notional_usd, usd_rate, eur_rate, tenor)

print(f"Net Present Value (NPV) of FX Swap:")
print(f"From USD Perspective: ${npv_usd:,.2f}")
print(f"From EUR Perspective: €{npv_eur:,.2f}")




import pandas as pd
import numpy as np

def compute_adjusted_fee(df,
                         vol_window=5,
                         vol_baseline_window=20,
                         memory_threshold=3,
                         alpha_smooth=0.03,
                         alpha_regime=0.10):
    """
    df must have columns: ['stock','date','fee','fee_second','price']
    Returns df with columns: ['fee_base','signal','memory','fee_adjusted']
    """
    df = df.sort_values(['stock', 'date']).copy()
    
    # 1. returns & rolling volatility
    df['r'] = df.groupby('stock')['price'].pct_change()
    df['vol'] = (df.groupby('stock')['r']
                   .transform(lambda x: x.rolling(vol_window, min_periods=2).std()))
    # baseline volatility for signal comparison
    df['vol_base'] = (df.groupby('stock')['vol']
                        .transform(lambda x: x.rolling(vol_baseline_window, min_periods=5).median()))
    
    # 2. weighted base fee
    df['fee_base'] = np.where(
        df['fee_second'] > df['fee'],
        0.7 * df['fee_second'] + 0.3 * df['fee'],
        0.5 * df['fee_second'] + 0.5 * df['fee']
    )
    
    # 3. directional signal S_t
    cond_increase = (df['r'] < 0) & (df['vol'] > df['vol_base'])
    cond_decrease = (df['r'] > 0) & (df['vol'] < df['vol_base'])
    df['signal'] = 0
    df.loc[cond_increase, 'signal'] = 1
    df.loc[cond_decrease, 'signal'] = -1
    
    # 4. memory counter M_t of consecutive nonzero signals
    def compute_memory(signal_series):
        mem = np.zeros_like(signal_series, dtype=int)
        count = 0
        prev = 0
        for i, s in enumerate(signal_series):
            if s != 0 and s == prev:
                count += 1
            elif s != 0:
                count = 1
            else:
                count = 0
            mem[i] = count
            prev = s if s != 0 else 0
        return mem

    df['memory'] = (df.groupby('stock')['signal']
                      .transform(lambda x: compute_memory(x.values)))
    
    # 5. final adjusted fee
    # if memory >= threshold → regime adjustment; else smooth adjustment
    use_regime = df['memory'] >= memory_threshold
    df['fee_adjusted'] = df['fee_base'] * (
        1 + np.where(use_regime, alpha_regime, alpha_smooth) * df['signal']
    )
    
    return df

# -------------------------
# Example usage:
# -------------------------
# df = pd.read_csv("your_data.csv", parse_dates=['date'])
# df_adj = compute_adjusted_fee(df)

# Now df_adj contains:
#  - fee_base     : your weighted anchor fee
#  - signal       : +1/0/–1 directional flags
#  - memory       : consecutive-day counts of same nonzero signal
#  - fee_adjusted : final smoothed & regime‑aware fee



import pandas as pd
import numpy as np

def build_fee_model(df,
                    fee_window=20,
                    price_window=20,
                    signal_window=3,
                    z_thresh=2,
                    base_weight_high=0.7,
                    alpha_smooth=0.02,
                    alpha_regime=0.08):
    """
    Assumes df has columns: ['stock', 'date', 'price', 'fee', 'fee_second']
    Returns df with additional columns, including the smoothed fee prediction: fee_pred
    """
    df = df.sort_values(['stock', 'date']).copy()
    
    # --- Compute return and rolling volatility of price ---
    df['return'] = df.groupby('stock')['price'].pct_change()
    df['price_vol'] = df.groupby('stock')['return'].transform(lambda x: x.rolling(price_window).std())
    df['price_mean'] = df.groupby('stock')['price'].transform(lambda x: x.rolling(price_window).mean())

    # --- Rolling statistics for fee ---
    df['fee_mean'] = df.groupby('stock')['fee'].transform(lambda x: x.rolling(fee_window).mean())
    df['fee_vol'] = df.groupby('stock')['fee'].transform(lambda x: x.rolling(fee_window).std())
    
    # --- Fee z-score for regime awareness ---
    df['fee_z'] = (df['fee'] - df['fee_mean']) / df['fee_vol']

    # --- Blended base fee ---
    df['fee_base'] = np.where(
        df['fee_second'] > df['fee'],
        base_weight_high * df['fee_second'] + (1 - base_weight_high) * df['fee'],
        0.5 * df['fee_second'] + 0.5 * df['fee']
    )

    # --- Signal definition: vol up + price down = increase; vol down + price up = decrease ---
    cond_up = (df['return'] < 0) & (df['price_vol'] > df['price_vol'].rolling(price_window).median())
    cond_down = (df['return'] > 0) & (df['price_vol'] < df['price_vol'].rolling(price_window).median())
    df['signal'] = 0
    df.loc[cond_up, 'signal'] = 1
    df.loc[cond_down, 'signal'] = -1

    # --- Count persistence of directional signal ---
    def count_signal(series):
        mem = np.zeros_like(series, dtype=int)
        count = 0
        prev = 0
        for i, s in enumerate(series):
            if s != 0 and s == prev:
                count += 1
            elif s != 0:
                count = 1
            else:
                count = 0
            mem[i] = count
            prev = s if s != 0 else 0
        return mem

    df['memory'] = df.groupby('stock')['signal'].transform(lambda x: count_signal(x.values))

    # --- Adjustment logic ---
    use_regime = (df['memory'] >= signal_window) | (df['fee_z'] > z_thresh)
    df['fee_pred'] = df['fee_base'] * (1 + np.where(use_regime, alpha_regime, alpha_smooth) * df['signal'])

    return df
