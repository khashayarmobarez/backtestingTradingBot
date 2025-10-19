import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===============================================================
#  STEP 1: LOAD AND PREPARE DATA
# ===============================================================

# Load CSV file (no header, since your first row is actual data)
data = pd.read_csv("gold_data.csv", header=None)

data = data.head(100)  # limit to first 500 rows for faster testing

# Assign standard column names
data.columns = ["date", "time", "open", "high", "low", "close", "volume"]

# Combine date + time into single datetime column
data["datetime"] = pd.to_datetime(data["date"] + " " + data["time"])

# Keep only the needed columns for trading
data = data[["datetime", "open", "high", "low", "close"]]

# Sort by datetime (in case data is out of order)
data.sort_values("datetime", inplace=True)
data.reset_index(drop=True, inplace=True)

print(f"✅ Data loaded successfully — {len(data)} candles available.\n")
print(data.head())  # optional: see structure

# ===============================================================
#  STEP 2: DEFINE THE BACKTESTING LOGIC
# ===============================================================

def backtest_candle_strategy(data, entry_offset=0.2, stop_offset=0.2):
    """
    Backtests a candle-based trading strategy on 4-hour candles.
    Opens one trade at the close of each candle and tracks performance until stop-loss is hit.
    """
    trades = []

    for i in range(len(data) - 1):
        candle = data.iloc[i]

        open_price = candle["open"]
        close_price = candle["close"]
        high_price = candle["high"]
        low_price = candle["low"]
        date = candle["datetime"]

        # Determine trade direction
        if close_price > open_price:  # Bullish candle → Buy
            trade_type = "Buy"
            entry = close_price + entry_offset
            stop_loss = low_price - stop_offset
        elif close_price < open_price:  # Bearish candle → Sell
            trade_type = "Sell"
            entry = close_price - entry_offset
            stop_loss = high_price + stop_offset
        else:
            # Skip doji (no direction)
            continue

        distance = abs(entry - stop_loss)
        max_profit = 0

        # Simulate forward candles to check when stop-loss is hit
        for j in range(i + 1, len(data)):
            future = data.iloc[j]
            high_future = future["high"]
            low_future = future["low"]

            if trade_type == "Buy":
                # Track the highest price before stop-loss is hit
                max_profit = max(max_profit, high_future - entry)
                if low_future <= stop_loss:
                    break

            elif trade_type == "Sell":
                # Track lowest price before stop-loss is hit
                max_profit = max(max_profit, entry - low_future)
                if high_future >= stop_loss:
                    break

        reward_risk = max_profit / distance if distance != 0 else np.nan

        # Record trade
        trades.append({
            "date": date,
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
