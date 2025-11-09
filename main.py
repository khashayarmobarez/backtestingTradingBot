import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===============================================================
#  STEP 1: LOAD AND PREPARE DATA
# ===============================================================

# Load CSV file (no header, since your first row is actual data)
data = pd.read_csv("gold_data.csv", header=None)

# data = data.head(1000)  # limit to first 500 rows for faster testing

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
print(data.head())

# ===============================================================
#  STEP 2: DEFINE THE BACKTESTING LOGIC
# ===============================================================

def backtest_candle_strategy(data, entry_offset=0.2, stop_offset=0.2):
    """
    Backtests a candle-based trading strategy on 4-hour candles.
    Opens one trade at the close of each candle and tracks performance until stop-loss is hit.
    If data ends before SL is hit, position is closed at end of data.
    """
    trades = []
    end_of_data_closes = 0

    for i in range(len(data) - 1):
        candle = data.iloc[i]

        open_price = candle["open"]
        close_price = candle["close"]
        high_price = candle["high"]
        low_price = candle["low"]
        datetime_obj = candle["datetime"]
        
        # Extract day of week (Monday, Tuesday, etc.)
        day_of_week = datetime_obj.strftime("%A")

        # Determine trade direction based on candle type
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

        # Calculate distance (risk)
        distance = abs(entry - stop_loss)
        max_profit = 0
        stop_hit = False
        candles_held = 0
        close_reason = "Stop Loss"
        reached_end = False

        # Simulate forward candles to check when stop-loss is hit
        for j in range(i + 1, len(data)):
            future = data.iloc[j]
            high_future = future["high"]
            low_future = future["low"]
            candles_held += 1

            # Check if this is the last candle in the data
            is_last_candle = (j == len(data) - 1)

            if trade_type == "Buy":
                # Track the highest profit before stop-loss is hit
                current_profit = high_future - entry
                max_profit = max(max_profit, current_profit)
                
                # Check if stop-loss is hit
                if low_future <= stop_loss:
                    stop_hit = True
                    close_reason = "Stop Loss"
                    break
                
                # If we reached the last candle without hitting SL
                if is_last_candle:
                    close_reason = "End of Data"
                    reached_end = True
                    end_of_data_closes += 1
                    break

            elif trade_type == "Sell":
                # Track the highest profit before stop-loss is hit
                current_profit = entry - low_future
                max_profit = max(max_profit, current_profit)
                
                # Check if stop-loss is hit
                if high_future >= stop_loss:
                    stop_hit = True
                    close_reason = "Stop Loss"
                    break
                
                # If we reached the last candle without hitting SL
                if is_last_candle:
                    close_reason = "End of Data"
                    reached_end = True
                    end_of_data_closes += 1
                    break

        # Calculate reward/risk ratio
        if distance != 0:
            reward_risk_value = max_profit / distance
            # If reward/risk < 1, mark as "SL"
            if reward_risk_value < 1:
                reward_risk = "SL"
            else:
                reward_risk = round(reward_risk_value, 2)
        else:
            reward_risk = "SL"

        # Record trade
        trades.append({
            "date": datetime_obj.strftime("%Y-%m-%d"),
            "time": datetime_obj.strftime("%H:%M:%S"),
            "day_of_week": day_of_week,
            "type": trade_type,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "distance": round(distance, 2),
            "max_profit": round(max_profit, 2),
            "reward_risk": reward_risk,
            "candles_held": candles_held,
            "close_reason": close_reason
        })

    return pd.DataFrame(trades), end_of_data_closes

# ===============================================================
#  STEP 3: RUN BACKTEST AND SAVE RESULTS
# ===============================================================

results, end_of_data_closes = backtest_candle_strategy(data)
results.to_csv("trades.csv", index=False)
print("💾 Results saved to trades.csv")

# ===============================================================
#  STEP 4: SUMMARY STATISTICS
# ===============================================================

total_trades = len(results)
stop_loss_trades = len(results[results["close_reason"] == "Stop Loss"])
end_of_data_trades = len(results[results["close_reason"] == "End of Data"])

# Calculate average R/R only for numeric values (exclude "SL")
numeric_rr = results[results["reward_risk"] != "SL"]["reward_risk"]
avg_rr = numeric_rr.mean() if len(numeric_rr) > 0 else 0

avg_profit = results["max_profit"].mean()
avg_candles_held = results["candles_held"].mean()
sl_count = len(results[results["reward_risk"] == "SL"])

print("\n📊 --- BACKTEST SUMMARY ---")
print(f"Total Trades: {total_trades}")
print(f"Closed by Stop Loss: {stop_loss_trades}")
print(f"Closed at End of Data: {end_of_data_trades}")
print(f"Trades with R/R < 1: {sl_count}")
print(f"Average Reward/Risk (excluding SL): {avg_rr:.2f}")
print(f"Average Max Profit: {avg_profit:.2f} USD")
print(f"Average Candles Held: {avg_candles_held:.1f} candles ({avg_candles_held * 4:.1f} hours)")

if end_of_data_trades > 0:
    print(f"\nℹ️  {end_of_data_trades} positions were closed because the last candle was reached.")
    print("These positions never hit their stop loss during the available data.")

# Analyze performance by day of week
print("\n📅 --- PERFORMANCE BY DAY OF WEEK ---")
day_stats = results.groupby("day_of_week").agg({
    "reward_risk": lambda x: x[x != "SL"].mean() if len(x[x != "SL"]) > 0 else 0,
    "max_profit": "mean",
    "type": "count"
}).round(2)
day_stats.columns = ["Avg R/R", "Avg Profit", "Trade Count"]

# Sort by day of week order
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_stats = day_stats.reindex([day for day in day_order if day in day_stats.index])
print(day_stats)

# Optional: visualize Reward/Risk distribution (numeric only)
if len(numeric_rr) > 0:
    plt.figure(figsize=(15, 5))
    
    # Subplot 1: R/R Distribution
    plt.subplot(1, 3, 1)
    plt.hist(numeric_rr, bins=30, color='gold', edgecolor='black')
    plt.title("Reward/Risk Distribution (R/R ≥ 1)")
    plt.xlabel("Reward/Risk Ratio")
    plt.ylabel("Frequency")
    
    # Subplot 2: Holding Period Distribution
    plt.subplot(1, 3, 2)
    plt.hist(results["candles_held"], bins=30, color='skyblue', edgecolor='black')
    plt.title("Holding Period Distribution")
    plt.xlabel("Candles Held")
    plt.ylabel("Frequency")
    
    # Subplot 3: Trades by Day of Week
    plt.subplot(1, 3, 3)
    day_counts = results["day_of_week"].value_counts().reindex(day_order, fill_value=0)
    plt.bar(range(len(day_counts)), day_counts.values, color='lightgreen', edgecolor='black')
    plt.xticks(range(len(day_counts)), [day[:3] for day in day_counts.index], rotation=45)
    plt.title("Trades by Day of Week")
    plt.xlabel("Day")
    plt.ylabel("Number of Trades")
    
    plt.tight_layout()
    plt.savefig('reward_risk_distribution.png')
    print("📊 Chart saved to: reward_risk_distribution.png")

# Optional: Show close reason breakdown
print("\n📋 --- CLOSE REASON BREAKDOWN ---")
print(results["close_reason"].value_counts())