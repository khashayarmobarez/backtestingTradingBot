import pandas as pd
import os

# ===============================================================
#  CATEGORIZE TRADING RESULTS BY DAY OF WEEK
# ===============================================================

def categorize_trades_by_day(input_csv="trades.csv", output_folder="categorized_by_weekdays_result"):
    """
    Categorizes trades from the backtest results:
    1. Separates Buy vs Sell positions
    2. Groups by day of the week (Monday, Tuesday, etc.)
    3. Sorts by reward/risk (small to large, SL at the end)
    
    Creates separate CSV files for each Buy/Sell + Day combination.
    """
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created folder: {output_folder}/")
    
    # Load the trades CSV
    try:
        trades = pd.read_csv(input_csv)
        print(f"✅ Loaded {len(trades)} trades from {input_csv}\n")
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        print("Please run main.py first to generate the trades.csv file.")
        return
    
    # Separate Buy and Sell positions
    buy_trades = trades[trades["type"] == "Buy"].copy()
    sell_trades = trades[trades["type"] == "Sell"].copy()
    
    # Get unique days of the week (in proper order)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    available_days = [day for day in day_order if day in trades["day_of_week"].unique()]
    
    print(f"📊 Buy Positions: {len(buy_trades)}")
    print(f"📊 Sell Positions: {len(sell_trades)}")
    print(f"📊 Trading Days: {', '.join(available_days)}\n")
    
    # Function to sort by reward/risk (SL goes to the end)
    def sort_by_reward_risk(df):
        # Separate numeric R/R and "SL" trades
        numeric_trades = df[df["reward_risk"] != "SL"].copy()
        sl_trades = df[df["reward_risk"] == "SL"].copy()
        
        # Sort numeric trades by reward_risk (ascending)
        numeric_trades = numeric_trades.sort_values("reward_risk", ascending=True)
        
        # Concatenate: numeric first, then SL
        return pd.concat([numeric_trades, sl_trades], ignore_index=True)
    
    # Counter for tracking files created
    files_created = 0
    
    # Process Buy positions
    print("🔵 Processing Buy positions...")
    for day in available_days:
        subset = buy_trades[buy_trades["day_of_week"] == day].copy()
        if len(subset) > 0:
            subset = sort_by_reward_risk(subset)
            
            filename = f"{output_folder}/buy_{day.lower()}.csv"
            subset.to_csv(filename, index=False)
            files_created += 1
            print(f"   ✓ Created: buy_{day.lower()}.csv ({len(subset)} trades)")
    
    # Process Sell positions
    print("\n🔴 Processing Sell positions...")
    for day in available_days:
        subset = sell_trades[sell_trades["day_of_week"] == day].copy()
        if len(subset) > 0:
            subset = sort_by_reward_risk(subset)
            
            filename = f"{output_folder}/sell_{day.lower()}.csv"
            subset.to_csv(filename, index=False)
            files_created += 1
            print(f"   ✓ Created: sell_{day.lower()}.csv ({len(subset)} trades)")
    
    # Summary statistics
    print(f"\n✅ COMPLETE! Created {files_created} categorized CSV files in '{output_folder}/'")
    
    # Create a summary report
    create_summary_report(trades, output_folder, day_order)


def create_summary_report(trades, output_folder, day_order):
    """
    Creates a summary report showing trade distribution across days of the week.
    """
    summary = []
    
    for trade_type in ["Buy", "Sell"]:
        type_trades = trades[trades["type"] == trade_type]
        
        for day in day_order:
            subset = type_trades[type_trades["day_of_week"] == day]
            
            if len(subset) > 0:
                # Calculate statistics
                total_trades = len(subset)
                sl_count = len(subset[subset["reward_risk"] == "SL"])
                numeric_rr = subset[subset["reward_risk"] != "SL"]["reward_risk"]
                avg_rr = numeric_rr.mean() if len(numeric_rr) > 0 else 0
                avg_profit = subset["max_profit"].mean()
                avg_distance = subset["distance"].mean()
                
                summary.append({
                    "Type": trade_type,
                    "Day": day,
                    "Total Trades": total_trades,
                    "SL Trades": sl_count,
                    "Avg R/R": round(avg_rr, 2),
                    "Avg Profit": round(avg_profit, 2),
                    "Avg Distance": round(avg_distance, 2)
                })
    
    summary_df = pd.DataFrame(summary)
    summary_file = f"{output_folder}/summary_report.csv"
    summary_df.to_csv(summary_file, index=False)
    
    print(f"\n📋 Summary Report:")
    print(summary_df.to_string(index=False))
    print(f"\n💾 Summary saved to: {summary_file}")


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  TRADING RESULTS CATEGORIZER - BY DAY OF WEEK")
    print("=" * 60)
    print()
    
    # Run the categorization
    categorize_trades_by_day(
        input_csv="trades.csv",
        output_folder="categorized_by_day"
    )
    
    print("\n" + "=" * 60)
    print("  All files ready! Check the 'categorized_by_day' folder.")
    print("=" * 60)