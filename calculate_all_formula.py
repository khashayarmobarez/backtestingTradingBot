import pandas as pd
import os
from datetime import datetime

# ===============================================================
#  APPLY FORMULA TO ALL TRADES
# ===============================================================

def calculate_profitability_formula(input_csv="trades.csv", output_csv="formula_results.csv"):
    """
    Applies the profitability formula to ALL trades in trades.csv.
    Returns all calculation results (not just positive ones).
    
    Formula for each TP (in order):
    (TP_value × remaining_TPs) - total_SLs
    
    Saves results to a CSV file.
    """
    
    # Load the trades CSV
    try:
        trades = pd.read_csv(input_csv)
        print(f"✅ Loaded {len(trades)} trades from {input_csv}\n")
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        print("Please run main.py first to generate the trades.csv file.")
        return
    
    # Convert reward_risk to string first to handle comparison
    trades["reward_risk"] = trades["reward_risk"].astype(str)
    
    # Extract numeric R/R values (TPs) - ignore "SL"
    tp_mask = trades["reward_risk"] != "SL"
    tps = trades[tp_mask]["reward_risk"].apply(lambda x: float(x)).tolist()
    
    # Count total SL trades
    initial_sl_count = len(trades[trades["reward_risk"] == "SL"])
    
    print(f"📊 Total Trades: {len(trades)}")
    print(f"📈 Total TPs (Profitable): {len(tps)}")
    print(f"📉 Total SLs (Stop Loss): {initial_sl_count}")
    print(f"\n{'='*60}")
    print("  APPLYING PROFITABILITY FORMULA")
    print(f"{'='*60}\n")
    
    # If no TPs at all, return early
    if len(tps) == 0:
        print("❌ No TPs found - All trades are SL")
        print("Cannot calculate formula.\n")
        return
    
    # Store all calculation results
    results = []
    current_sl_count = initial_sl_count
    
    # Iterate through each TP
    for i, tp_value in enumerate(tps):
        remaining_tps = len(tps) - i
        
        # Apply formula: (TP × remaining_TPs) - total_SLs
        result = (tp_value * remaining_tps) - current_sl_count
        
        # Store the calculation
        results.append({
            "Step": i + 1,
            "TP_Value": round(tp_value, 2),
            "Remaining_TPs": remaining_tps,
            "Total_SLs": current_sl_count,
            "Formula": f"({tp_value:.2f} × {remaining_tps}) - {current_sl_count}",
            "Result": round(result, 2),
            "Status": "✅ Positive" if result > 0 else "❌ Negative/Zero"
        })
        
        # Print the calculation
        print(f"Step {i+1}: ({tp_value:.2f} × {remaining_tps}) - {current_sl_count} = {result:.2f}")
        
        # Count this TP as SL for next iteration
        current_sl_count += 1
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    results_df.to_csv(output_csv, index=False)
    
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    # Calculate summary statistics
    positive_results = results_df[results_df["Result"] > 0]
    negative_results = results_df[results_df["Result"] <= 0]
    
    print(f"Total Calculations: {len(results_df)}")
    print(f"✅ Positive Results: {len(positive_results)}")
    print(f"❌ Negative/Zero Results: {len(negative_results)}")
    
    if len(positive_results) > 0:
        print(f"\nHighest Positive Result: {positive_results['Result'].max():.2f}")
        print(f"Lowest Positive Result: {positive_results['Result'].min():.2f}")
        print(f"Average Positive Result: {positive_results['Result'].mean():.2f}")
    
    if len(negative_results) > 0:
        print(f"\nLowest Negative Result: {negative_results['Result'].min():.2f}")
    
    print(f"\n💾 Results saved to: {output_csv}")
    print(f"{'='*60}\n")
    
    # Display all results
    print("📋 ALL CALCULATION RESULTS:")
    print(results_df.to_string(index=False))
    
    return results_df


def create_detailed_report(input_csv="trades.csv", output_txt="formula_report.txt"):
    """
    Creates a detailed text report of the formula calculations.
    """
    
    # Load trades
    try:
        trades = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        return
    
    # Convert reward_risk to string
    trades["reward_risk"] = trades["reward_risk"].astype(str)
    
    # Extract TPs and SLs
    tp_mask = trades["reward_risk"] != "SL"
    tps = trades[tp_mask]["reward_risk"].apply(lambda x: float(x)).tolist()
    initial_sl_count = len(trades[trades["reward_risk"] == "SL"])
    
    # Create report
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("  PROFITABILITY FORMULA REPORT - ALL TRADES")
    report_lines.append("=" * 70)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Source File: {input_csv}")
    report_lines.append("")
    report_lines.append(f"Total Trades: {len(trades)}")
    report_lines.append(f"Total TPs (Profitable Trades): {len(tps)}")
    report_lines.append(f"Total SLs (Stop Loss Trades): {initial_sl_count}")
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("  FORMULA CALCULATIONS")
    report_lines.append("=" * 70)
    report_lines.append("")
    
    if len(tps) == 0:
        report_lines.append("❌ No TPs found - All trades resulted in Stop Loss")
        report_lines.append("Cannot perform formula calculations.")
    else:
        current_sl_count = initial_sl_count
        all_results = []
        
        for i, tp_value in enumerate(tps):
            remaining_tps = len(tps) - i
            result = (tp_value * remaining_tps) - current_sl_count
            all_results.append(result)
            
            status = "✅ POSITIVE" if result > 0 else "❌ NEGATIVE/ZERO"
            
            report_lines.append(f"Step {i+1}:")
            report_lines.append(f"  TP Value: {tp_value:.2f}")
            report_lines.append(f"  Remaining TPs: {remaining_tps}")
            report_lines.append(f"  Total SLs: {current_sl_count}")
            report_lines.append(f"  Formula: ({tp_value:.2f} × {remaining_tps}) - {current_sl_count}")
            report_lines.append(f"  Result: {result:.2f}  {status}")
            report_lines.append("")
            
            current_sl_count += 1
        
        # Summary
        report_lines.append("=" * 70)
        report_lines.append("  SUMMARY")
        report_lines.append("=" * 70)
        report_lines.append("")
        report_lines.append(f"Total Calculations: {len(all_results)}")
        
        positive_results = [r for r in all_results if r > 0]
        negative_results = [r for r in all_results if r <= 0]
        
        report_lines.append(f"Positive Results: {len(positive_results)}")
        report_lines.append(f"Negative/Zero Results: {len(negative_results)}")
        
        if positive_results:
            report_lines.append("")
            report_lines.append(f"Highest Positive Result: {max(positive_results):.2f}")
            report_lines.append(f"Lowest Positive Result: {min(positive_results):.2f}")
            report_lines.append(f"Average Positive Result: {sum(positive_results)/len(positive_results):.2f}")
        
        if negative_results:
            report_lines.append("")
            report_lines.append(f"Lowest Negative Result: {min(negative_results):.2f}")
        
        report_lines.append("")
        report_lines.append("All Results (in order):")
        report_lines.append(", ".join([f"{r:.2f}" for r in all_results]))
    
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("  END OF REPORT")
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
    print("  PROFITABILITY FORMULA CALCULATOR - ALL TRADES")
    print("=" * 70)
    print()
    
    # Calculate formula for all trades
    results = calculate_profitability_formula(
        input_csv="trades.csv",
        output_csv="formula_results.csv"
    )
    
    # Create detailed text report
    print()
    create_detailed_report(
        input_csv="trades.csv",
        output_txt="formula_report.txt"
    )
    
    print("\n" + "=" * 70)
    print("  COMPLETE!")
    print("=" * 70)
    print("\n📂 Files created:")
    print("  • formula_results.csv  (Spreadsheet with all calculations)")
    print("  • formula_report.txt   (Detailed text report)")
    print()