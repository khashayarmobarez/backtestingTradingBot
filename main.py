import pandas as pd
import matplotlib.pyplot as plt

# ========================================
# 1️⃣ LOAD AND PREPARE DATA
# ========================================
data = pd.read_csv("gold_data.csv")

# Rename columns clearly (adapt to your CSV structure)
data.columns = ["Date", "Time", "Open", "High", "Low", "Close", "Extra"]

# Combine Date + Time into one datetime column
data["Datetime"] = pd.to_datetime(data["Date"] + " " + data["Time"])

# Keep only relevant columns
data = data[["Datetime", "Open", "High", "Low", "Close"]]

# Sort chronologically
data = data.sort_values("Datetime").reset_index(drop=True)

print(f"✅ Data loaded successfully! Total candles: {len(data)}")
print("Sample data:\n", data.head(), "\n")

# ========================================
# 2️⃣ STRATEGY PARAMETERS
# ========================================
# You can tweak these to test performance later
SHORT_MA = 5
LONG_MA = 20
INITIAL_BALANCE = 10000  # Starting balance in USD
POSITION_SIZE = 1.0      # Buy 1 unit (e.g., 1 oz gold) per trade

# ========================================
# 3️⃣ CALCULATE INDICATORS
# ========================================
data["SMA_Short"] = data["Close"].rolling(SHORT_MA).mean()
data["SMA_Long"] = data["Close"].rolling(LONG_MA).mean()

# Signal logic: if short > long → uptrend → buy
data["Signal"] = 0
data.loc[data["SMA_Short"] > data["SMA_Long"], "Signal"] = 1
data.loc[data["SMA_Short"] < data["SMA_Long"], "Signal"] = -1

# Shift signal so we enter at the *next candle*, not the same one
data["Signal"] = data["Signal"].shift(1)

# ========================================
# 4️⃣ BACKTEST LOOP (REALISTIC SIMULATION)
# ========================================
balance = INITIAL_BALANCE   # how much money we have
position = 0                # 0 = no trade, 1 = long, -1 = short
entry_price = 0             # track price we entered at
trade_log = []              # list of all trades

# Loop through the data row by row
for i in range(1, len(data)):
    price = data.loc[i, "Close"]
    signal = data.loc[i, "Signal"]
    date = data.loc[i, "Datetime"]

    # === BUY SIGNAL ===
    if signal == 1 and position == 0:
        position = 1
        entry_price = price
        trade_log.append({
            "Type": "BUY",
            "Date": date,
            "Price": price,
            "BalanceBefore": balance
        })
        print(f"🟢 BUY at {price:.2f} on {date}")

    # === SELL SIGNAL (if we were holding long) ===
    elif signal == -1 and position == 1:
        profit = (price - entry_price) * POSITION_SIZE
        balance += profit
        trade_log.append({
            "Type": "SELL",
            "Date": date,
            "Price": price,
            "Profit": profit,
            "BalanceAfter": balance
        })
        print(f"🔴 SELL at {price:.2f} on {date} | Profit: {profit:.2f} | New Balance: {balance:.2f}")
        position = 0

# ========================================
# 5️⃣ FINAL RESULTS
# ========================================
# If we still have a position open at the end, close it at last price
if position == 1:
    final_price = data["Close"].iloc[-1]
    profit = (final_price - entry_price) * POSITION_SIZE
    balance += profit
    print(f"⚪ Closing final position at {final_price:.2f}, profit: {profit:.2f}")
    position = 0

# Print trade summary
print("\n==============================")
print("📊 FINAL TRADING REPORT")
print("==============================")
print(f"Total Trades: {len(trade_log)}")
print(f"Final Balance: {balance:.2f} USD")
print(f"Total Profit/Loss: {balance - INITIAL_BALANCE:.2f} USD")
print("==============================\n")

# Convert trade log to DataFrame for later analysis
trades = pd.DataFrame(trade_log)

# Save trade log to CSV
trades.to_csv("trade_log.csv", index=False)
print("💾 Trade log saved as trade_log")

# ========================================
# 6️⃣ PLOT CHART
# ========================================
plt.figure(figsize=(12, 6))
plt.plot(data["Datetime"], data["Close"], label="Gold Price", color="gold", alpha=0.7)
plt.plot(data["Datetime"], data["SMA_Short"], label=f"SMA {SHORT_MA}", color="blue", alpha=0.7)
plt.plot(data["Datetime"], data["SMA_Long"], label=f"SMA {LONG_MA}", color="red", alpha=0.7)

# Add buy/sell points
plt.scatter(trades[trades["Type"] == "BUY"]["Date"], trades[trades["Type"] == "BUY"]["Price"], marker="^", color="green", label="BUY", s=80)
plt.scatter(trades[trades["Type"] == "SELL"]["Date"], trades[trades["Type"] == "SELL"]["Price"], marker="v", color="red", label="SELL", s=80)

plt.legend()
plt.title("Gold SMA Crossover Trading Backtest")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid(True)
plt.show()
