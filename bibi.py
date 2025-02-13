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
