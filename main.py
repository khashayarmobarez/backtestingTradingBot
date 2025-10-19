import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===============================================================
#  STEP 1: LOAD AND PREPARE DATA
# ===============================================================

# File name of your historical data
DATA_FILE = "gold_data.csv"

# Read CSV (adjust if your file has no headers)
data = pd.read_csv(DATA_FILE)

# --- Data cleaning section ---
# Your data likely has columns like:
# Date, Time, Open, High, Low, Close, Volume
# Let's handle cases where headers are missing or weird.
if len(data.columns) <= 6:
    data.columns = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]

# Combine date & time into single datetime
data["datetime"] = pd.to_datetime(data["Date"] + " " + data["Time"])
data = data[["datetime", "Open", "High", "Low", "Close"]]  # keep only needed
data.sort_values("datetime", inplace=True)
data.reset_index(drop=True, inplace=True)

print(f"✅ Data loaded successfully — {len(data)} candles available.")


# ===============================================================
#  STEP 2: DEFINE THE BACKTESTING LOGIC
# ===============================================================

def backtest_candle_strategy(data, entry_offset=0.2, stop_offset=0.2):
    """
    Simulates the candle-based strategy on 4-hour candles.
    Opens one trade per candle at close based on candle direction.
    """
    trades = []  # list to store trade info

    for i in range(len(data) - 1):  # exclude last candle (no next candles to check)
        current = data.iloc[i]
        current_date = current["datetime"]
        current_open = current["Open"]
        current_high = current["High"]
        current_low = current["Low"]
        current_close = current["Close"]

        # --- Determine trade type ---
        if current_close > current_open:
            trade_type = "Buy"
            entry = current_close + entry_offset
            stop_loss = current_low - stop_offset
        elif current_close < current_open:
            trade_type = "Sell"
            entry = current_close - entry_offset
            stop_loss = current_high + stop_offset
        else:
            # Skip if it's a doji candle (open == close)
            continue

        # Distance between entry and stop-loss
        distance = abs(entry - stop_loss)

        # --- Simulate forward candles until stop loss hit ---
        max_profit = 0
        for j in range(i + 1, len(data)):
            future = data.iloc[j]
            high = future["High"]
            low = future["Low"]

            if trade_type == "Buy":
                # Calculate max profit so far
                max_profit = max(max_profit, high - entry)
                # Check if stop loss hit
                if low <= stop_loss:
                    break

            elif trade_type == "Sell":
                # Calculate max profit so far (for sell it's entry - low)
                max_profit = max(max_profit, entry - low)
                # Check if stop loss hit
                if high >= stop_loss:
                    break

        # Reward/Risk ratio
        reward_risk = max_profit / distance if distance != 0 else np.nan

        # Record trade
        trades.append({
            "date": current_date,
            "type": trade_type,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "distance": round(distance, 2),
            "max_profit": round(max_profit, 2),
            "reward_risk": round(reward_risk, 2)
        })

    return pd.DataFrame(trades)


# ===============================================================
#  STEP 3: RUN BACKTEST AND SAVE RESULTS
# ===============================================================

results = backtest_candle_strategy(data)
results.to_csv("trades.csv", index=False)
print("💾 Results saved to trades.csv")

# ===============================================================
#  STEP 4: SUMMARY STATISTICS
# ===============================================================

total_trades = len(results)
avg_rr = results["reward_risk"].mean()
avg_profit = results["max_profit"].mean()

print("\n📊 --- BACKTEST SUMMARY ---")
print(f"Total Trades: {total_trades}")
print(f"Average Reward/Risk: {avg_rr:.2f}")
print(f"Average Max Profit: {avg_profit:.2f} USD")

# Optional: visualize Reward/Risk distribution
plt.hist(results["reward_risk"], bins=30, color='gold', edgecolor='black')
plt.title("Reward/Risk Distribution")
plt.xlabel("Reward/Risk Ratio")
plt.ylabel("Frequency")
plt.show()
