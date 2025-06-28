# Generate Key Charts for README
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Configure plotting
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

print("Generating synthetic data and charts...")

# Define simulation parameters
SIMULATION_DAYS = 180
START_DATE = pd.Timestamp('2024-01-01')
INITIAL_PORTFOLIO_VALUE = 100_000_000

# Currency parameters
currency_params = {
    'USD': {'initial_rate': 1.0000, 'annual_vol': 0.00, 'drift': 0.0000},
    'EUR': {'initial_rate': 1.0850, 'annual_vol': 0.12, 'drift': -0.0010},
    'GBP': {'initial_rate': 1.2650, 'annual_vol': 0.14, 'drift': -0.0015},
    'JPY': {'initial_rate': 0.0067, 'annual_vol': 0.11, 'drift': -0.0005},
    'EM_BASKET': {'initial_rate': 0.8500, 'annual_vol': 0.18, 'drift': -0.0020}
}

# Portfolio weights
portfolio_weights = {
    'USD': 0.45, 'EUR': 0.25, 'GBP': 0.10, 'JPY': 0.12, 'EM_BASKET': 0.08
}

def generate_fx_rates(currencies, params, days, start_date):
    dates = pd.date_range(start=start_date, periods=days, freq='D')
    fx_data = pd.DataFrame(index=dates)
    dt = 1/252
    
    for currency in currencies:
        if currency == 'USD':
            fx_data[currency] = 1.0
            continue
        
        S0 = params[currency]['initial_rate']
        sigma = params[currency]['annual_vol']
        mu = params[currency]['drift']
        
        np.random.seed(42 + hash(currency) % 100)
        dW = np.random.normal(0, np.sqrt(dt), days)
        
        rates = np.zeros(days)
        rates[0] = S0
        
        for t in range(1, days):
            rates[t] = rates[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW[t])
        
        fx_data[currency] = rates
    
    return fx_data

def generate_portfolio_data():
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'EM_BASKET']
    fx_rates = generate_fx_rates(currencies, currency_params, SIMULATION_DAYS, START_DATE)
    fx_returns = fx_rates.pct_change().dropna()
    
    # Generate synthetic portfolio values for different hedge ratios
    dates = fx_rates.index
    portfolio_values = pd.DataFrame(index=dates)
    
    # Simulate different performance based on hedge ratios
    base_return = 0.0003  # Daily base return
    
    for i, (strategy, hedge_ratio) in enumerate([('Unhedged (0%)', 0.0), ('Partial Hedge (50%)', 0.5), ('Full Hedge (100%)', 1.0)]):
        values = np.zeros(len(dates))
        values[0] = INITIAL_PORTFOLIO_VALUE
        
        for j in range(1, len(dates)):
            # Simulate portfolio returns with different FX exposure
            fx_impact = 0
            for currency in ['EUR', 'GBP', 'JPY', 'EM_BASKET']:
                weight = portfolio_weights[currency]
                fx_change = fx_returns[currency].iloc[j-1] if not pd.isna(fx_returns[currency].iloc[j-1]) else 0
                fx_impact += weight * fx_change * (1 - hedge_ratio)
            
            daily_return = base_return + fx_impact + np.random.normal(0, 0.008)
            values[j] = values[j-1] * (1 + daily_return)
        
        portfolio_values[strategy] = values
    
    return fx_rates, portfolio_values

# Generate the data
fx_rates, portfolio_values = generate_portfolio_data()

# Create images directory
import os
if not os.path.exists('images'):
    os.makedirs('images')

print("Creating Chart 1: FX Rates Evolution...")
# Chart 1: FX Rates Evolution
plt.figure(figsize=(12, 6))
for currency in ['EUR', 'GBP', 'JPY', 'EM_BASKET']:
    normalized_rates = fx_rates[currency] / fx_rates[currency].iloc[0]
    plt.plot(fx_rates.index, normalized_rates, label=currency, linewidth=2)

plt.title('FX Rates Evolution (Normalized to Day 1)', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Normalized FX Rate')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/fx_rates_evolution.png', dpi=300, bbox_inches='tight')
plt.close()

print("Creating Chart 2: Portfolio Performance...")
# Chart 2: Portfolio Value Evolution
plt.figure(figsize=(12, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
for i, (strategy, color) in enumerate(zip(portfolio_values.columns, colors)):
    plt.plot(portfolio_values.index, portfolio_values[strategy] / 1e6, 
             label=strategy, linewidth=2.5, color=color)

plt.title('Portfolio Value Evolution by Hedge Strategy', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($ Millions)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/portfolio_performance.png', dpi=300, bbox_inches='tight')
plt.close()

print("Creating Chart 3: Risk-Return Analysis...")
# Chart 3: Risk-Return Profile (simulated data)
returns_data = []
vol_data = []
strategies = list(portfolio_values.columns)

for strategy in strategies:
    returns = portfolio_values[strategy].pct_change().dropna()
    annual_return = returns.mean() * 252 * 100
    annual_vol = returns.std() * np.sqrt(252) * 100
    returns_data.append(annual_return)
    vol_data.append(annual_vol)

plt.figure(figsize=(10, 6))
colors = ['red', 'orange', 'green']
for i, strategy in enumerate(strategies):
    plt.scatter(vol_data[i], returns_data[i], s=200, label=strategy, 
               color=colors[i], alpha=0.7)
    plt.annotate(strategy, (vol_data[i], returns_data[i]), 
                xytext=(5, 5), textcoords='offset points', fontsize=9)

plt.title('Risk-Return Profile', fontsize=14, fontweight='bold')
plt.xlabel('Annual Volatility (%)')
plt.ylabel('Annual Return (%)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/risk_return_profile.png', dpi=300, bbox_inches='tight')
plt.close()

print("All charts generated successfully!")
print("Charts saved in 'images/' directory:")
print("- fx_rates_evolution.png")
print("- portfolio_performance.png") 
print("- risk_return_profile.png") 