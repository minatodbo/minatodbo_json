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
