import pandas as pd
import numpy as np

# ===============================================================
#  CALCULATE LOWEST DRAWDOWN FOR EACH REWARD LEVEL
# ===============================================================

def calculate_lowest_drawdown(input_csv="trades.csv", output_csv="lowest_drawdown_results.csv"):
    """
    Calculates the lowest possible cumulative value for each reward level.
    
    Algorithm:
    1. First pass: Go through entire list from top to bottom, track when balance = 0
    2. Second pass: Start from each zero-crossing position and calculate drawdown
    3. Return the absolute lowest across all passes (including initial pass)
    
    For each reward level (1, 2, 3, etc.):
    - Counts trades >= reward as +reward_value
    - Counts trades < reward as -1
    - Tracks the lowest cumulative value reached
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
    print(f"📈 Max Reward/Risk: {trades['rr_numeric'].max():.2f}\n")
    
    # Determine reward levels to test (integers from 1 to max)
    max_reward = int(trades["rr_numeric"].max())
    reward_levels = list(range(1, max_reward + 1))
    
    print(f"🔢 Testing reward levels: {reward_levels}\n")
    print("=" * 70)
    print("  CALCULATING LOWEST DRAWDOWN FOR EACH REWARD LEVEL")
    print("=" * 70)
    
    results = []
    
    # Test each reward level
    for reward_idx, reward_level in enumerate(reward_levels, 1):
        print(f"\n📍 Reward Level {reward_level} ({reward_idx}/{len(reward_levels)}):")
        print(f"   Rules: R/R ≥ {reward_level} = +{reward_level}, R/R < {reward_level} = -1")
        
        # PHASE 1: Initial pass through entire list
        print(f"   🔄 Phase 1: Initial pass through all trades...")
        
        running_total = 0
        lowest_overall = 0
        zero_crossing_positions = []  # Positions where balance reaches exactly 0
        
        for i in range(len(trades)):
            rr_value = trades.iloc[i]["rr_numeric"]
            
            if rr_value >= reward_level:
                running_total += reward_level
            else:
                running_total -= 1
            
            # Track the lowest point
            if running_total < lowest_overall:
                lowest_overall = running_total
            
            # Mark positions where balance reaches exactly 0
            if running_total == 0:
                for j in range(i + 1, len(trades)):
                    if trades.iloc[j]["reward_risk"] == "SL":
                        next_sl_idx = j
                        break
                if next_sl_idx is not None:
                    zero_crossing_positions.append(next_sl_idx)
        
        print(f"   ✅ Initial pass complete - Lowest: {lowest_overall}")
        print(f"   📌 Found {len(zero_crossing_positions)} zero-crossing positions")
        
        best_starting_position = 0  # Default to start
        
        # PHASE 2: Test from each zero-crossing position
        if len(zero_crossing_positions) > 0:
            print(f"   🔄 Phase 2: Testing from zero-crossing positions...")
            
            # Calculate progress reporting interval
            total_positions = len(zero_crossing_positions)
            report_interval = min(max(total_positions // 10, 1), 100)
            
            for idx, start_idx in enumerate(zero_crossing_positions, 1):
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
                if lowest_in_this_run < lowest_overall:
                    lowest_overall = lowest_in_this_run
                    best_starting_position = start_idx
                
                # Log progress periodically
                if idx % report_interval == 0 or idx == total_positions:
                    progress_pct = (idx / total_positions) * 100
                    print(f"   ⏳ Progress: {idx}/{total_positions} positions tested ({progress_pct:.1f}%) - Current lowest: {lowest_overall}")
            
            print(f"   ✅ Phase 2 complete")
        else:
            print(f"   ℹ️  No zero-crossing positions found - using initial pass result")
        
        print(f"   🎯 ABSOLUTE LOWEST: {lowest_overall}")
        print(f"   📍 Worst Starting Position: Index {best_starting_position}")
        
        results.append({
            "Reward_Level": reward_level,
            "Absolute_Lowest": lowest_overall,
            "Starting_Position": best_starting_position,
            "Zero_Crossings": len(zero_crossing_positions)
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
    report_lines.append(f"Reward Levels Tested: {reward_levels}")
    report_lines.append("")
    report_lines.append("Algorithm:")
    report_lines.append("  1. Initial pass through entire list (index 0 to end)")
    report_lines.append("  2. Mark positions where balance reaches exactly 0")
    report_lines.append("  3. Test from each zero-crossing position")
    report_lines.append("  4. Return absolute lowest across all passes")
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("  RESULTS BY REWARD LEVEL")
    report_lines.append("=" * 70)
    report_lines.append("")
    
    # Calculate for each reward level
    for reward_idx, reward_level in enumerate(reward_levels, 1):
        print(f"   📍 Processing Reward Level {reward_level} ({reward_idx}/{len(reward_levels)})...")
        
        # Phase 1: Initial pass
        running_total = 0
        lowest_overall = 0
        zero_crossing_positions = []
        
        for i in range(len(trades)):
            rr_value = trades.iloc[i]["rr_numeric"]
            
            if rr_value >= reward_level:
                running_total += reward_level
            else:
                running_total -= 1
            
            if running_total < lowest_overall:
                lowest_overall = running_total
            
            if running_total == 0:
                zero_crossing_positions.append(i)
        
        best_starting_position = 0
        
        # Phase 2: Test from zero crossings
        if len(zero_crossing_positions) > 0:
            total_positions = len(zero_crossing_positions)
            report_interval = min(max(total_positions // 10, 1), 100)
            
            for idx, start_idx in enumerate(zero_crossing_positions, 1):
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
                
                if lowest_in_this_run < lowest_overall:
                    lowest_overall = lowest_in_this_run
                    best_starting_position = start_idx
                
                if idx % report_interval == 0:
                    progress_pct = (idx / total_positions) * 100
                    print(f"      Progress: {progress_pct:.0f}% complete...")
        
        report_lines.append(f"Reward Level {reward_level}:")
        report_lines.append(f"  Rule: R/R ≥ {reward_level} = +{reward_level}, R/R < {reward_level} = -1")
        report_lines.append(f"  Absolute Lowest Drawdown: {lowest_overall}")
        report_lines.append(f"  Worst Starting Position: Index {best_starting_position}")
        report_lines.append(f"  Zero-Crossing Positions Found: {len(zero_crossing_positions)}")
        report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append("  INTERPRETATION")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append("The 'Absolute Lowest' value represents the maximum drawdown")
    report_lines.append("(lowest cumulative value) you could experience when trading")
    report_lines.append("at that reward level.")
    report_lines.append("")
    report_lines.append("Zero-crossing positions are points where the cumulative balance")
    report_lines.append("reaches exactly 0 during the initial pass through all trades.")
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
    print("  LOWEST DRAWDOWN CALCULATOR - ZERO-CROSSING METHOD")
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