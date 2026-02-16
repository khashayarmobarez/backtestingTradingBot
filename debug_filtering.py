import pandas as pd
import math

def calculate_list_score(trades_df, rr_threshold):
    """
    Calculate the score for a list of trades based on R/R threshold.
    """
    score = 0

    for rr in trades_df["reward_risk"]:
        if rr == "SL":
            score -= 1
        else:
            rr_value = float(rr)
            if rr_value > rr_threshold:
                score += rr_threshold
            else:
                score -= 1

    # Apply trade count penalty
    trade_count = len(trades_df)
    penalty = math.floor(trade_count / 20)
    score -= penalty

    return score

# Check specific dates
dates_to_check = ["2009-02-25", "2009-02-26", "2009-02-27", "2009-03-05"]

print("=" * 70)
print("DEBUGGING FILTERING PROCESS")
print("=" * 70)
print()

# Load the main trades file
trades_df = pd.read_csv("trades.csv")

print("Step 1: Checking trades in original file")
print("-" * 70)
for date in dates_to_check:
    date_trades = trades_df[trades_df["date"] == date]
    print(f"\n{date}: {len(date_trades)} trades")
    for idx, row in date_trades.iterrows():
        print(f"  {row['time']} | {row['type']} | distance={row['distance']:.2f} | R/R={row['reward_risk']}")

# Check buy_distance_8.csv
print("\n\n" + "=" * 70)
print("Step 2: Checking buy_distance_8.csv")
print("=" * 70)

buy_8_df = pd.read_csv("categorized_by_distance_results/buy_distance_8.csv")
print(f"\nTotal trades in buy_distance_8.csv: {len(buy_8_df)}")

for date in dates_to_check:
    date_trades = buy_8_df[buy_8_df["date"] == date]
    if len(date_trades) > 0:
        print(f"\n{date}: {len(date_trades)} trades")
        for idx, row in date_trades.iterrows():
            print(f"  {row['time']} | {row['type']} | distance={row['distance']:.2f} | R/R={row['reward_risk']}")

# Calculate score for buy_distance_8 with RR threshold = 1
score = calculate_list_score(buy_8_df, 1)
print(f"\n\nScore for buy_distance_8.csv (RR threshold=1): {score}")
print(f"Trade count: {len(buy_8_df)}, Penalty: {math.floor(len(buy_8_df) / 20)}")

# Check if it passes
if score > 0:
    print("✓ PASSED distance filter")
else:
    print("✗ FILTERED OUT at distance level")

# Now check hour filtering
print("\n\n" + "=" * 70)
print("Step 3: Checking hour-level filtering")
print("=" * 70)

# Extract hour from time column
buy_8_df["hour"] = buy_8_df["time"].apply(lambda x: x.split(":")[0])

# Check specific hours
for date in dates_to_check:
    date_trades = buy_8_df[buy_8_df["date"] == date]
    if len(date_trades) > 0:
        for idx, row in date_trades.iterrows():
            hour = row["hour"]
            hour_trades = buy_8_df[buy_8_df["hour"] == hour]
            hour_score = calculate_list_score(hour_trades, 1)
            status = "✓ PASSED" if hour_score > 0 else "✗ FILTERED OUT"
            print(f"\n{date} {row['time']} | Hour {hour}: {len(hour_trades)} trades, Score={hour_score} {status}")
