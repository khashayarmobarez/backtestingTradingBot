import pandas as pd
import numpy as np

# ===============================================================
#  CALCULATE LOWEST DRAWDOWN FOR EACH REWARD LEVEL
# ===============================================================

def calculate_lowest_drawdown(input_csv="trades.csv", output_csv="lowest_drawdown_results.csv"):
    """
    Calculates the lowest possible cumulative value for each reward level.
    
    For each reward level (1, 2, 3, etc.):
    - Starts from each SL position in the list
    - Counts trades >= reward as +reward_value
    - Counts trades < reward as -1
    - Tracks the lowest cumulative value reached
    
    Returns the absolute lowest value for each reward level.
    """
    
    # Load the trades CSV
    try:
        trades = pd.read_csv(input_csv)
        print(f"✅ Loaded {len(trades)} trades from {input_csv}\n")
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        return
    
    # Convert reward_risk to handle both numeric and "SL"
    trades["reward_risk"] = trades["reward_risk"].astype(str)
    
    # Create a numeric version for calculations (SL = 0)
    def convert_to_numeric(rr):
        if rr == "SL":
            return 0.0
        else:
            return float(rr)
    
    trades["rr_numeric"] = trades["reward_risk"].apply(convert_to_numeric)
    
    print(f"📊 Total Trades: {len(trades)}")
    print(f"📉 Total SLs: {len(trades[trades['reward_risk'] == 'SL'])}")
    print(f"📈 Max Reward/Risk: {trades['rr_numeric'].max():.2f}")
    
    # Find all SL positions
    sl_positions = trades[trades["reward_risk"] == "SL"].index.tolist()
    
    if len(sl_positions) == 0:
        print("\n❌ No SL trades found in the list!")
        return
    
    print(f"🎯 Found {len(sl_positions)} SL positions to test from\n")
    
    # Determine reward levels to test (integers from 1 to max)
    max_reward = int(trades["rr_numeric"].max())
    reward_levels = list(range(1, max_reward + 1))
    
    print(f"🔢 Testing reward levels: {reward_levels}\n")
    print("=" * 70)
    print("  CALCULATING LOWEST DRAWDOWN FOR EACH REWARD LEVEL")
    print("=" * 70)
    
    results = []
    
    # Test each reward level
    for reward_level in reward_levels:
        print(f"\n📍 Reward Level {reward_level}:")
        print(f"   Rules: R/R ≥ {reward_level} = +{reward_level}, R/R < {reward_level} = -1")
        
        absolute_lowest = float('inf')  # Start with infinity
        best_starting_position = None
        
        # Test starting from each SL position
        for start_idx in sl_positions:
            running_total = 0
            lowest_in_this_run = 0
            
            # Go through all trades from this starting position
            for i in range(start_idx, len(trades)):
                rr_value = trades.iloc[i]["rr_numeric"]
                
                if rr_value >= reward_level:
                    running_total += reward_level
                else:
                    running_total -= 1
                
                # Track the lowest point
                if running_total < lowest_in_this_run:
                    lowest_in_this_run = running_total
            
            # Update absolute lowest if this run was lower
            if lowest_in_this_run < absolute_lowest:
                absolute_lowest = lowest_in_this_run
                best_starting_position = start_idx
        
        print(f"   ✅ Absolute Lowest: {absolute_lowest}")
        print(f"   📌 Best Starting Position: Index {best_starting_position}")
        
        results.append({
            "Reward_Level": reward_level,
            "Absolute_Lowest": absolute_lowest,
            "Starting_Position": best_starting_position
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    results_df.to_csv(output_csv, index=False)
    
    print("\n" + "=" * 70)
    print("  SUMMARY - LOWEST DRAWDOWN BY REWARD LEVEL")
    print("=" * 70)
    print()
    print(results_df.to_string(index=False))
    print()
    print(f"💾 Results saved to: {output_csv}")
    
    return results_df


def create_detailed_report(input_csv="trades.csv", output_txt="drawdown_report.txt"):
    """
    Creates a detailed text report of the drawdown analysis.
    """
    
    # Load trades
    try:
        trades = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        return
    
    # Convert reward_risk
    trades["reward_risk"] = trades["reward_risk"].astype(str)
    
    def convert_to_numeric(rr):
        if rr == "SL":
            return 0.0
        else:
            return float(rr)
    
    trades["rr_numeric"] = trades["reward_risk"].apply(convert_to_numeric)
    
    # Find SL positions
    sl_positions = trades[trades["reward_risk"] == "SL"].index.tolist()
    
    if len(sl_positions) == 0:
        print("❌ No SL trades found!")
        return
    
    # Determine reward levels
    max_reward = int(trades["rr_numeric"].max())
    reward_levels = list(range(1, max_reward + 1))
    
    # Create report
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("  LOWEST DRAWDOWN ANALYSIS REPORT")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append(f"Total Trades: {len(trades)}")
    report_lines.append(f"Total SL Positions: {len(sl_positions)}")
    report_lines.append(f"Reward Levels Tested: {reward_levels}")
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("  RESULTS BY REWARD LEVEL")
    report_lines.append("=" * 70)
    report_lines.append("")
    
    # Calculate for each reward level
    for reward_level in reward_levels:
        absolute_lowest = float('inf')
        best_starting_position = None
        
        for start_idx in sl_positions:
            running_total = 0
            lowest_in_this_run = 0
            
            for i in range(start_idx, len(trades)):
                rr_value = trades.iloc[i]["rr_numeric"]
                
                if rr_value >= reward_level:
                    running_total += reward_level
                else:
                    running_total -= 1
                
                if running_total < lowest_in_this_run:
                    lowest_in_this_run = running_total
            
            if lowest_in_this_run < absolute_lowest:
                absolute_lowest = lowest_in_this_run
                best_starting_position = start_idx
        
        report_lines.append(f"Reward Level {reward_level}:")
        report_lines.append(f"  Rule: R/R ≥ {reward_level} = +{reward_level}, R/R < {reward_level} = -1")
        report_lines.append(f"  Absolute Lowest Drawdown: {absolute_lowest}")
        report_lines.append(f"  Best Starting Position: Index {best_starting_position}")
        report_lines.append(f"  Total SL Positions Tested: {len(sl_positions)}")
        report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append("  INTERPRETATION")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append("The 'Absolute Lowest' value represents the maximum drawdown")
    report_lines.append("(lowest cumulative value) you could experience when trading")
    report_lines.append("at that reward level, starting from the worst possible position.")
    report_lines.append("")
    report_lines.append("A lower (more negative) number means higher risk at that level.")
    report_lines.append("=" * 70)
    
    # Save to file
    with open(output_txt, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"📄 Detailed report saved to: {output_txt}")


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LOWEST DRAWDOWN CALCULATOR")
    print("=" * 70)
    print()
    
    # Calculate lowest drawdown for all reward levels
    results = calculate_lowest_drawdown(
        input_csv="trades.csv",
        output_csv="lowest_drawdown_results.csv"
    )
    
    # Create detailed text report
    print()
    create_detailed_report(
        input_csv="trades.csv",
        output_txt="drawdown_report.txt"
    )
    
    print("\n" + "=" * 70)
    print("  COMPLETE!")
    print("=" * 70)
    print("\n📂 Files created:")
    print("  • lowest_drawdown_results.csv  (Summary results)")
    print("  • drawdown_report.txt          (Detailed report)")
    print()