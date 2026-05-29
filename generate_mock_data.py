import pandas as pd
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Generate mock model_output.xlsx
model_data = {
    'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
    'Signal': ['Strong Buy', 'Buy', 'Hold', 'Sell'],
    'Target Weight': [0.15, 0.10, 0.05, 0.00],
    'Current Weight': [0.10, 0.12, 0.05, 0.02]
}
df_model = pd.DataFrame(model_data)
df_model.to_excel('data/model_output.xlsx', index=False)

# Generate mock trades.xlsx
trades_data = {
    'Id': ['TRD-001', 'TRD-002', 'TRD-003', 'TRD-004'],
    'Date': ['2023-10-25', '2023-10-25', '2023-10-26', '2023-10-26'],
    'Ticker': ['AAPL', 'MSFT', 'TSLA', 'AMZN'],
    'Action': ['BUY', 'SELL', 'SELL', 'BUY'],
    'Quantity': [100, 50, 200, 10],
    'Price': [170.50, 330.20, 210.00, 130.00]
}
df_trades = pd.DataFrame(trades_data)
df_trades.to_excel('data/trades.xlsx', index=False)
