import numpy as np
import plotly.graph_objs as go
import plotly.io as pio

# Set your renderer (you can choose "browser" or "notebook" depending on your environment)
pio.renderers.default = "browser"

# Example maturities dictionary (in years)
maturities = {
    "Tbill1M": 1/12,    # ~0.0833 years
    "Tbill3M": 3/12,    # 0.25 years
    "Tbill6M": 6/12,    # 0.5 years
    "Tbill12M": 12/12   # 1.0 year
}

# Create an empty Plotly figure
fig = go.Figure()

# Loop through each T-Bill bucket
for tbill, T in maturities.items():
    sim_paths = simulated_rates[tbill]  # shape: (N_simulations, N_steps+1)
    N_steps = sim_paths.shape[1] - 1
    time_axis = np.linspace(0, T, N_steps + 1)
    
    # Plot a subset (e.g., 10 sample paths) to avoid cluttering the plot
    for i in range(min(10, sim_paths.shape[0])):
        fig.add_trace(
            go.Scatter(
                x=time_axis, 
                y=sim_paths[i],
                mode='lines',
                name=f'{tbill} Path {i+1}',
                line=dict(width=1),
                opacity=0.7,
                showlegend=False  # Hide individual path legends
            )
        )
    
    # Overlay a horizontal line for the market yield for this T-Bill (using the last observed yield)
    market_yield = df_yields[tbill].iloc[-1]
    fig.add_trace(
        go.Scatter(
            x=[0, T],
            y=[market_yield, market_yield],
            mode='lines',
            name=f'{tbill} Market Yield',
            line=dict(dash='dash', width=2)
        )
    )

# Update layout for clarity
fig.update_layout(
    title="Simulated Interest Rate Paths vs. Market Yields for T-Bills",
    xaxis_title="Time (Years)",
    yaxis_title="Yield (in decimal form)",
    template="plotly_dark"
)

# Show the interactive plot
fig.show()




import numpy as np
import matplotlib.pyplot as plt

# --- 1. Define Simulation Settings ---
r0 = 0.05                  # Current rate, e.g., 5% (in decimal)
cut_threshold = r0 - 0.0025  # Define a cut as a drop of 25bps (0.25%)
T = 1.0                    # Simulation horizon: 1 year
N_steps = 250              # Number of time steps (daily steps, roughly)
N_sim = 10000              # Number of Monte Carlo simulations

# CIR model parameters (example values – calibrate these from historical data)
kappa = 0.5                # Mean reversion speed
theta = 0.05               # Long-term mean rate; here assumed equal to r0 for simplicity
sigma = 0.1                # Volatility (annualized)

# --- 2. Define the CIR Simulation Function ---
def simulate_cir_paths(r0, kappa, theta, sigma, T, N_steps, N_sim):
    """
    Simulate short-rate paths using the CIR model.
    
    Parameters:
        r0: Initial rate.
        kappa: Mean reversion speed.
        theta: Long-term mean rate.
        sigma: Volatility.
        T: Time horizon (in years).
        N_steps: Number of time steps.
        N_sim: Number of simulations.
    
    Returns:
        rates: A NumPy array of shape (N_sim, N_steps+1) containing the simulated rate paths.
    """
    dt = T / N_steps
    rates = np.zeros((N_sim, N_steps + 1))
    rates[:, 0] = r0
    
    for i in range(1, N_steps + 1):
        dW = np.random.normal(0, np.sqrt(dt), N_sim)
        # Ensure non-negative rates using np.maximum:
        rates[:, i] = np.maximum(
            rates[:, i-1] + kappa * (theta - rates[:, i-1]) * dt + sigma * np.sqrt(np.maximum(rates[:, i-1], 0)) * dW,
            0
        )
    return rates

# --- 3. Run the Simulation ---
simulated_paths = simulate_cir_paths(r0, kappa, theta, sigma, T, N_steps, N_sim)

# --- 4. Assess the Cut Probability ---
# For each simulated path, compute the minimum rate over the time horizon.
min_rates = simulated_paths.min(axis=1)

# Calculate the probability that the rate falls below the cut threshold at any time.
prob_cut = np.mean(min_rates < cut_threshold)
print(f"Estimated probability of a Fed rate cut (≥25bps) within 1 year: {prob_cut:.2%}")

# --- 5. Visualize Some Sample Paths ---
import plotly.graph_objs as go
import plotly.io as pio
pio.renderers.default = "browser"

# Generate a time axis (in years)
time_axis = np.linspace(0, T, N_steps+1)

fig = go.Figure()
# Plot a few sample paths (e.g., 20 paths)
for i in range(min(20, N_sim)):
    fig.add_trace(go.Scatter(
        x=time_axis, 
        y=simulated_paths[i],
        mode='lines',
        name=f'Path {i+1}',
        opacity=0.6,
        showlegend=False
    ))

# Add a horizontal line for the cut threshold
fig.add_trace(go.Scatter(
    x=[0, T],
    y=[cut_threshold, cut_threshold],
    mode='lines',
    name='Cut Threshold',
    line=dict(dash='dash', color='red')
))

fig.update_layout(
    title="Sample CIR Simulated Short-Rate Paths with Cut Threshold",
    xaxis_title="Time (Years)",
    yaxis_title="Interest Rate",
    template="plotly_dark"
)
fig.show()


from scipy.optimize import minimize

def cir_log_likelihood(params, rates, dt):
    """
    Compute the negative log-likelihood for CIR model.

    Parameters:
        params: Tuple (kappa, theta, sigma) to be estimated
        rates: Historical interest rate data (Pandas Series)
        dt: Time step (e.g., 1/252 for daily data)

    Returns:
        Negative log-likelihood value
    """
    kappa, theta, sigma = params
    n = len(rates)
    ll = 0.0

    for t in range(1, n):
        mean = rates[t-1] + kappa * (theta - rates[t-1]) * dt
        variance = sigma**2 * rates[t-1] * dt
        ll += -0.5 * np.log(2 * np.pi * variance) - 0.5 * ((rates[t] - mean) ** 2 / variance)

    return -ll  # Negative for minimization

# Initial guess for parameters
initial_params = [0.1, np.mean(daily_yields), np.std(np.diff(daily_yields))]

# Minimize the negative log-likelihood
res = minimize(cir_log_likelihood, initial_params, args=(daily_yields, 1/252), method='L-BFGS-B')

# Extract estimated parameters
kappa_mle, theta_mle, sigma_mle = res.x


print(f"MLE Estimated kappa: {kappa_mle:.4f}")
print(f"MLE Estimated theta: {theta_mle:.4%}")
print(f"MLE Estimated sigma: {sigma_mle:.4%}")






import numpy as np
from scipy.optimize import fsolve

def bond_price(ytm, face_value, coupon_rate, years_to_maturity, price, frequency=2):
    """
    Bond pricing formula used in YTM computation.
    
    Parameters:
        ytm : float  -> Yield to Maturity (as a decimal, per year)
        face_value : float  -> Par value of the bond (typically $1,000 for Treasuries)
        coupon_rate : float  -> Annual coupon rate (e.g., 0.03 for 3%)
        years_to_maturity : float  -> Years remaining until maturity
        price : float  -> Current bond price in the market
        frequency : int  -> Number of coupon payments per year (default = 2 for U.S. Treasuries)

    Returns:
        Difference between computed bond price and actual market price (for fsolve)
    """
    periods = int(years_to_maturity * frequency)  # Total number of periods
    coupon = (coupon_rate / frequency) * face_value  # Coupon per period
    ytm_per_period = ytm / frequency  # Adjust YTM for frequency

    # Present value of coupon payments
    pv_coupons = sum([coupon / (1 + ytm_per_period) ** t for t in range(1, periods + 1)])

    # Present value of face value
    pv_face_value = face_value / (1 + ytm_per_period) ** periods

    return pv_coupons + pv_face_value - price

def compute_ytm(price, face_value, coupon_rate, years_to_maturity, frequency=2):
    """
    Computes Yield to Maturity (YTM) using numerical root finding.
    
    Parameters:
        price : float  -> Current bond price in USD
        face_value : float  -> Par value of the bond (typically $1,000)
        coupon_rate : float  -> Annual coupon rate as a decimal (e.g., 0.03 for 3%)
        years_to_maturity : float  -> Number of years until maturity
        frequency : int  -> Number of coupon payments per year (default = 2 for U.S. Treasuries)

    Returns:
        ytm : float  -> Yield to Maturity as a decimal (e.g., 0.035 for 3.5%)
    """
    # Initial guess for YTM (use current yield as a starting point)
    initial_guess = coupon_rate

    # Solve for YTM using fsolve
    ytm_solution = fsolve(bond_price, initial_guess, args=(face_value, coupon_rate, years_to_maturity, price, frequency))

    return ytm_solution[0]  # Extract solution

# --- Example: Compute YTM for a U.S. Treasury Bond ---
price = 970  # Market price of the bond ($970)
face_value = 1000  # Par value ($1,000 for Treasuries)
coupon_rate = 0.03  # 3% annual coupon rate (e.g., a 3% Treasury)
years_to_maturity = 5  # 5 years to maturity
frequency = 2  # U.S. Treasuries pay semi-annually

ytm = compute_ytm(price, face_value, coupon_rate, years_to_maturity, frequency)
print(f"Computed Yield to Maturity (YTM): {ytm:.4%}")  # Convert to percentage format


import numpy as np
from scipy.optimize import brentq

# Given Data
price = 100.41  # Market price
face_value = 100  # Par value
coupon_rate = 4.875 / 100  # Annual coupon rate (4.875%)
years_to_maturity = 0.7726  # Time to maturity in years
frequency = 2  # Semi-annual payments

# Compute Coupon and Number of Periods
coupon = (coupon_rate / frequency) * face_value  # Semi-annual coupon
N = years_to_maturity * frequency  # Total number of periods (fractional)
integer_N = int(N)  # Whole number of periods
fractional_N = N - integer_N  # Remaining fractional period

# Define Bond Price Function
def bond_price_ytm(ytm):
    ytm_per_period = ytm / frequency  # Convert to semi-annual rate
    
    # Present value of all full coupon payments
    pv_coupons = sum([coupon / (1 + ytm_per_period) ** t for t in range(1, integer_N + 1)])
    
    # Discounting for fractional period (last coupon + face value)
    discount_factor = (1 + ytm_per_period) ** (integer_N + fractional_N)
    pv_face_value = (coupon + face_value) / discount_factor
    
    return pv_coupons + pv_face_value - price  # Difference from market price

# Solve for YTM using Brent's Method (Higher Precision)
ytm_solution = brentq(bond_price_ytm, 0.01, 0.1)  # Bounds between 1% and 10%
ytm_annualized = ytm_solution * 100  # Convert to percentage

print(f"Computed YTM: {ytm_annualized:.5f}%")

