import numpy as np
import matplotlib.pyplot as plt

# Constants
FUTURES_PRICE = 101.50  # Futures settlement price
CTD_BOND_PRICE = 100.25  # Cheapest-to-Deliver bond price (clean price)
COUPON_RATE = 0.03875  # Coupon rate (3.875%)
COUPON_PER_DAY = COUPON_RATE / 360  # Daily coupon accrual
REPO_RATE = 0.021  # Initial repo rate (2.1% annualized)
REPO_VOLATILITY = 0.005  # Repo rate volatility (0.5%)
BOND_PRICE_VOLATILITY = 0.02  # Bond price volatility (2% per day)
NUM_SIMULATIONS = 10000  # Number of Monte Carlo simulations
DELIVERY_DAYS = 10  # Delivery window (days)
REPO_COST_PER_DAY = CTD_BOND_PRICE * REPO_RATE / 360  # Repo cost per day

# Initialize random number generator
np.random.seed(42)

# Simulate Monte Carlo paths
def simulate_monte_carlo():
    # Store optimal delivery days for each simulation
    optimal_delivery_days = []

    for _ in range(NUM_SIMULATIONS):
        repo_rate = REPO_RATE
        bond_price = CTD_BOND_PRICE
        accrued_coupon = 0  # Starts with no coupon accrual

        # Track daily carry (net carry) for each path
        net_carry = []

        # Simulate the 10-day delivery window
        for day in range(1, DELIVERY_DAYS + 1):
            # Accrued coupon (simple linear accumulation)
            accrued_coupon = COUPON_PER_DAY * day

            # Simulate repo rate and bond price for the day
            repo_rate += np.random.normal(0, REPO_VOLATILITY)  # Repo rate evolution (mean reversion)
            bond_price += np.random.normal(0, BOND_PRICE_VOLATILITY)  # Bond price evolution (random walk)

            # Calculate repo cost for the day
            repo_cost = bond_price * repo_rate / 360

            # Calculate net carry for this day
            net_carry.append(accrued_coupon - repo_cost)

        # Choose the day with the maximum net carry
        optimal_day = np.argmax(net_carry) + 1  # +1 because day index starts from 1
        optimal_delivery_days.append(optimal_day)

    # Return the optimal delivery days for all simulations
    return optimal_delivery_days

# Run the simulation
optimal_delivery_days = simulate_monte_carlo()

# Analyze the results
delivery_day_counts = np.bincount(optimal_delivery_days)[1:]  # Count deliveries per day, ignore index 0
optimal_day_distribution = delivery_day_counts / NUM_SIMULATIONS  # Normalize to get a probability distribution

# Output results
print("Optimal delivery day distribution:")
for i, prob in enumerate(optimal_day_distribution, 1):
    print(f"Day {i}: {prob * 100:.2f}%")

# Plot the results
plt.bar(range(1, DELIVERY_DAYS + 1), optimal_day_distribution * 100, color='b', alpha=0.7)
plt.xlabel('Delivery Day')
plt.ylabel('Probability (%)')
plt.title('Monte Carlo Simulation: Optimal Bond Futures Delivery Day')
plt.show()
