import pandas as pd
import matplotlib.pyplot as plt

# Load CSV without header
data = pd.read_csv("gold_data.csv", header=None)

# Assign proper column names
data.columns = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]

# Combine Date + Time into one datetime column
data["DateTime"] = pd.to_datetime(data["Date"] + " " + data["Time"])

# Set index
data.set_index("DateTime", inplace=True)

# Example: Simple moving average strategy
data["SMA_10"] = data["Close"].rolling(window=10).mean()
data["SMA_30"] = data["Close"].rolling(window=30).mean()

# Generate signals
data["Signal"] = 0
data.loc[data["SMA_10"] > data["SMA_30"], "Signal"] = 1
data.loc[data["SMA_10"] < data["SMA_30"], "Signal"] = -1

# Plot
plt.figure(figsize=(12,6))
plt.plot(data.index, data["Close"], label="Gold Price")
plt.plot(data.index, data["SMA_10"], label="SMA 10")
plt.plot(data.index, data["SMA_30"], label="SMA 30")
plt.legend()
plt.show()
