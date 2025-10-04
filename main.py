import pandas as pd
import matplotlib.pyplot as plt

# reading the codes
# ===============================
# 1. LOAD THE DATA
# ===============================
# Change the filename if your CSV has a different name
data = pd.read_csv("gold_data.csv")

# Let's print the first rows so we know what we’re working with
print("Raw data sample:")
print(data.head())

# ===============================
# 2. CLEAN & PREPARE THE DATA
# ===============================

# Your CSV has columns like: Date, Time, Open, High, Low, Close, Volume
# But sometimes headers are messy, so let's rename them clearly:
data.columns = ["Date", "Time", "Open", "High", "Low", "Close", "Extra"]

# Merge Date + Time into one datetime column
data["Datetime"] = pd.to_datetime(data["Date"] + " " + data["Time"])

# Drop unused columns
data = data[["Datetime", "Open", "High", "Low", "Close"]]

# Make sure rows are sorted by time
data = data.sort_values("Datetime").reset_index(drop=True)

# ===============================
# 3. DEFINE A SIMPLE STRATEGY
# ===============================
# We’ll use Moving Average Crossover:
# - Short MA (fast) = 5 periods
# - Long MA (slow) = 20 periods
# When short > long → BUY signal
# When short < long → SELL signal

data["SMA5"] = data["Close"].rolling(window=5).mean()
data["SMA20"] = data["Close"].rolling(window=20).mean()

# ===============================
# 4. CREATE TRADING SIGNALS
# ===============================
# Buy = 1, Sell = -1, Hold = 0
data["Signal"] = 0
data.loc[data["SMA5"] > data["SMA20"], "Signal"] = 1
data.loc[data["SMA5"] < data["SMA20"], "Signal"] = -1

# Shift signal to avoid "future knowledge" (you can only act on next candle)
data["Position"] = data["Signal"].shift(1)

# ===============================
# 5. BACKTESTING
# ===============================
# Strategy return = % change of Close * position
data["Return"] = data["Close"].pct_change()
data["StrategyReturn"] = data["Return"] * data["Position"]

# Calculate total performance
cumulative_return = (1 + data["StrategyReturn"].fillna(0)).cumprod()

# ===============================
# 6. PLOT RESULTS
# ===============================
plt.figure(figsize=(12,6))
plt.plot(data["Datetime"], data["Close"], label="Gold Price", alpha=0.6)
plt.plot(data["Datetime"], data["SMA5"], label="SMA 5", alpha=0.8)
plt.plot(data["Datetime"], data["SMA20"], label="SMA 20", alpha=0.8)

# Mark buy & sell signals
plt.scatter(data[data["Position"] == 1]["Datetime"], 
            data[data["Position"] == 1]["Close"], 
            label="Buy", marker="^", color="g", alpha=1)

plt.scatter(data[data["Position"] == -1]["Datetime"], 
            data[data["Position"] == -1]["Close"], 
            label="Sell", marker="v", color="r", alpha=1)

plt.legend()
plt.title("Gold Trading Strategy (SMA Crossover)")
plt.show()

# ===============================
# 7. FINAL PERFORMANCE REPORT
# ===============================
print("\nFinal Results:")
print("Total Strategy Return: {:.2f}%".format((cumulative_return.iloc[-1] - 1) * 100))
print("Buy & Hold Return: {:.2f}%".format((data["Close"].iloc[-1] / data["Close"].iloc[0] - 1) * 100))
