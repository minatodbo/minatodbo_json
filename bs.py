def implied_volatility_refined(S, K, T, r, market_price, option_type):
    def price_difference(sigma):
        return black_scholes(S, K, T, r, sigma, option_type) - market_price

    # Intrinsic value for deep ITM/OTM detection
    intrinsic_value = max(S - K, 0) if option_type == 'C' else max(K - S, 0)

    # If market price is very close to intrinsic value, fallback to a rough approximation
    if market_price <= intrinsic_value:
        return 0.001  # Near-zero volatility

    # Try Brent's method with expanded range
    try:
        return brentq(price_difference, 0.001, 10.0, xtol=1e-8)
    except ValueError:
        # If Brent fails, use fallback approximation
        initial_iv = (market_price - intrinsic_value) / (S * np.sqrt(2 * np.pi * T))
        print("Fallback IV Approximation:", initial_iv)
        return initial_iv

# Re-run the calculation
iv = implied_volatility_refined(S, K, T, r, market_price, option_type)
if np.isnan(iv):
    print("Failed to compute implied volatility.")
else:
    print(f"Implied Volatility: {iv:.4%}")
