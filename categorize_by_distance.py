import pandas as pd
import os
import math

# ===============================================================
#  CATEGORIZE AND SPLIT TRADING RESULTS
# ===============================================================

def categorize_trades(input_csv="trades.csv", output_folder="categorized_by_distance_results"):
    """
    Categorizes trades from the backtest results:
    1. Separates Buy vs Sell positions
    2. Groups by distance value (rounded down to nearest integer)
    3. Sorts by reward/risk (small to large, SL at the end)
    
    Creates separate CSV files for each Buy/Sell + Distance combination.
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
    
    # Round distance to 1 decimal place
    trades["distance"] = trades["distance"].apply(lambda x: round(x, 1))
    
    # Add a column for rounded-down distance
    trades["distance_rounded"] = trades["distance"].apply(lambda x: math.floor(x))
    
    # Separate Buy and Sell positions
    buy_trades = trades[trades["type"] == "Buy"].copy()
    sell_trades = trades[trades["type"] == "Sell"].copy()
    
    print(f"📊 Buy Positions: {len(buy_trades)}")
    print(f"📊 Sell Positions: {len(sell_trades)}")
    print(f"📊 Unique Distance Values: {sorted(trades['distance_rounded'].unique())}\n")
    
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
    for distance_val in sorted(buy_trades["distance_rounded"].unique()):
        subset = buy_trades[buy_trades["distance_rounded"] == distance_val].copy()
        subset = sort_by_reward_risk(subset)
        
        filename = f"{output_folder}/buy_distance_{distance_val}.csv"
        subset.to_csv(filename, index=False)
        files_created += 1
        print(f"   ✓ Created: buy_distance_{distance_val}.csv ({len(subset)} trades)")
    
    # Process Sell positions
    print("\n🔴 Processing Sell positions...")
    for distance_val in sorted(sell_trades["distance_rounded"].unique()):
        subset = sell_trades[sell_trades["distance_rounded"] == distance_val].copy()
        subset = sort_by_reward_risk(subset)
        
        filename = f"{output_folder}/sell_distance_{distance_val}.csv"
        subset.to_csv(filename, index=False)
        files_created += 1
        print(f"   ✓ Created: sell_distance_{distance_val}.csv ({len(subset)} trades)")
    
    # Summary statistics
    print(f"\n✅ COMPLETE! Created {files_created} categorized CSV files in '{output_folder}/'")
    
    # Create a summary report
    create_summary_report(trades, output_folder)


def create_summary_report(trades, output_folder):
    """
    Creates a summary report showing trade distribution across categories.
    """
    summary = []
    
    for trade_type in ["Buy", "Sell"]:
        type_trades = trades[trades["type"] == trade_type]
        
        for distance_val in sorted(type_trades["distance_rounded"].unique()):
            subset = type_trades[type_trades["distance_rounded"] == distance_val]
            
            # Calculate statistics
            total_trades = len(subset)
            sl_count = len(subset[subset["reward_risk"] == "SL"])
            numeric_rr = subset[subset["reward_risk"] != "SL"]["reward_risk"]
            avg_rr = numeric_rr.mean() if len(numeric_rr) > 0 else 0
            avg_profit = subset["max_profit"].mean()
            
            summary.append({
                "Type": trade_type,
                "Distance": distance_val,
                "Total Trades": total_trades,
                "SL Trades": sl_count,
                "Avg R/R": round(avg_rr, 2),
                "Avg Profit": round(avg_profit, 2)
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
    print("  TRADING RESULTS CATEGORIZER")
    print("=" * 60)
    print()
    
    # Run the categorization
    categorize_trades(
        input_csv="trades.csv",
        output_folder="categorized_results"
    )
    
    print("\n" + "=" * 60)
    print("  All files ready! Check the 'categorized_results' folder.")
    print("=" * 60)