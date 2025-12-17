import pandas as pd
import os

def compare_and_extract_removed_trades(
    main_file="trades.csv",
    filtered_file="../version_2_Level_1_filtered_results/rr_threshold_1/final_result_rr_1.csv",
    output_file="removed_trades_rr_1.csv"
):
    """
    Compare the main trades file with the filtered RR=1 results and extract removed trades.
    
    This function identifies which trades were filtered out during the Level 1 filtering process.
    It compares trades based on date, time, and type (Buy/Sell) to determine which ones
    were removed.
    
    Process:
    1. Load the main trades.csv file (all original trades)
    2. Load the filtered RR=1 result file (trades that survived filtering)
    3. Compare them to find which trades were removed
    4. Save the removed trades to a CSV file
    
    Args:
        main_file (str): Path to the original trades.csv file
        filtered_file (str): Path to the final_result_rr_1.csv file
        output_file (str): Name of the output file for removed trades
    
    Returns:
        DataFrame: The removed trades as a pandas DataFrame
    
    Example:
        If main file has 1000 trades and filtered file has 300 trades,
        this function will return the 700 trades that were removed.
    """
    
    print("=" * 70)
    print("  COMPARING TRADES AND EXTRACTING REMOVED ONES")
    print("=" * 70)
    print()
    
    # Step 1: Load the main trades file
    print(f"📂 Loading main trades file: {main_file}")
    try:
        main_trades = pd.read_csv(main_file)
        print(f"   ✅ Loaded {len(main_trades)} trades from main file")
    except FileNotFoundError:
        print(f"   ❌ Error: {main_file} not found!")
        return None
    except Exception as e:
        print(f"   ❌ Error loading main file: {e}")
        return None
    
    # Step 2: Load the filtered RR=1 result file
    print(f"\n📂 Loading filtered RR=1 file: {filtered_file}")
    try:
        filtered_trades = pd.read_csv(filtered_file)
        print(f"   ✅ Loaded {len(filtered_trades)} trades from filtered file")
    except FileNotFoundError:
        print(f"   ❌ Error: {filtered_file} not found!")
        print(f"   💡 Make sure you've run the Level 1 filtering first!")
        return None
    except Exception as e:
        print(f"   ❌ Error loading filtered file: {e}")
        return None
    
    # Step 3: Create unique identifiers for comparison
    # We'll use a combination of date + time + type to identify each trade
    print(f"\n🔍 Comparing trades by date, time, and type...")
    
    # Create a unique identifier column for main trades
    # Format: "2015-12-24_06:30:00_Buy"
    main_trades['trade_id'] = (
        main_trades['date'].astype(str) + '_' + 
        main_trades['time'].astype(str) + '_' + 
        main_trades['type'].astype(str)
    )
    
    # Create the same identifier for filtered trades
    filtered_trades['trade_id'] = (
        filtered_trades['date'].astype(str) + '_' + 
        filtered_trades['time'].astype(str) + '_' + 
        filtered_trades['type'].astype(str)
    )
    
    # Step 4: Find trades that are in main but NOT in filtered
    # This gives us the removed trades
    kept_trade_ids = set(filtered_trades['trade_id'])
    
    # Filter main_trades to only include trades that are NOT in the kept set
    removed_trades = main_trades[~main_trades['trade_id'].isin(kept_trade_ids)].copy()
    
    # Remove the temporary trade_id column before saving
    removed_trades = removed_trades.drop(columns=['trade_id'])
    
    # Step 5: Display statistics
    print(f"\n📊 Comparison Results:")
    print(f"   • Total trades in main file: {len(main_trades)}")
    print(f"   • Trades kept after filtering: {len(filtered_trades)}")
    print(f"   • Trades removed: {len(removed_trades)}")
    print(f"   • Removal rate: {(len(removed_trades) / len(main_trades) * 100):.2f}%")
    
    # Breakdown by Buy/Sell
    if not removed_trades.empty:
        buy_removed = len(removed_trades[removed_trades['type'] == 'Buy'])
        sell_removed = len(removed_trades[removed_trades['type'] == 'Sell'])
        print(f"\n   📉 Removed trades breakdown:")
        print(f"      • Buy trades removed: {buy_removed}")
        print(f"      • Sell trades removed: {sell_removed}")
        
        # Breakdown by close reason
        if 'close_reason' in removed_trades.columns:
            print(f"\n   📋 Removed trades by close reason:")
            close_reason_counts = removed_trades['close_reason'].value_counts()
            for reason, count in close_reason_counts.items():
                print(f"      • {reason}: {count}")
        
        # Breakdown by reward_risk (SL vs numeric)
        if 'reward_risk' in removed_trades.columns:
            sl_count = len(removed_trades[removed_trades['reward_risk'] == 'SL'])
            numeric_count = len(removed_trades[removed_trades['reward_risk'] != 'SL'])
            print(f"\n   💰 Removed trades by result:")
            print(f"      • Stop Loss (SL): {sl_count}")
            print(f"      • Profit taken: {numeric_count}")
    
    # Step 6: Save the removed trades to a CSV file
    if not removed_trades.empty:
        # Sort by date and time for better readability
        removed_trades = removed_trades.sort_values(by=['date', 'time'])
        
        removed_trades.to_csv(output_file, index=False)
        print(f"\n✅ Removed trades saved to: {output_file}")
    else:
        print(f"\n⚠️  No trades were removed (all trades passed the filter)")
    
    print("\n" + "=" * 70)
    print("  ✅ COMPARISON COMPLETE!")
    print("=" * 70)
    
    return removed_trades


def compare_multiple_rr_thresholds(
    main_file="trades.csv",
    base_folder="../version_2_Level_1_filtered_results",
    output_folder="removed_trades_analysis"
):
    """
    Compare the main trades file with ALL RR threshold results.
    Creates separate removed trades files for each RR threshold.
    
    This is useful if you want to analyze what was removed at each RR level.
    
    Args:
        main_file (str): Path to the original trades.csv file
        base_folder (str): Path to the Level 1 filtered results folder
        output_folder (str): Folder to save all removed trades files
    
    Returns:
        dict: Dictionary mapping RR thresholds to their removed trades DataFrames
    """
    
    print("=" * 70)
    print("  COMPARING ALL RR THRESHOLDS")
    print("=" * 70)
    print()
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created output folder: {output_folder}/\n")
    
    results = {}
    
    # Iterate through all RR threshold folders
    for folder_name in sorted(os.listdir(base_folder)):
        folder_path = os.path.join(base_folder, folder_name)
        
        if not os.path.isdir(folder_path) or not folder_name.startswith("rr_threshold_"):
            continue
        
        # Extract RR threshold number
        rr_threshold = folder_name.replace("rr_threshold_", "")
        
        # Find the final result file
        final_file = None
        for filename in os.listdir(folder_path):
            if filename.startswith("final_result_rr_") and filename.endswith(".csv"):
                final_file = os.path.join(folder_path, filename)
                break
        
        if final_file is None:
            print(f"⚠️  No final result file found for RR threshold {rr_threshold}")
            continue
        
        # Compare and extract removed trades
        output_file = os.path.join(output_folder, f"removed_trades_rr_{rr_threshold}.csv")
        
        print(f"\n{'=' * 70}")
        print(f"  Processing RR Threshold: {rr_threshold}")
        print(f"{'=' * 70}")
        
        removed = compare_and_extract_removed_trades(
            main_file=main_file,
            filtered_file=final_file,
            output_file=output_file
        )
        
        results[rr_threshold] = removed
    
    print(f"\n\n{'=' * 70}")
    print("  ✅ ALL COMPARISONS COMPLETE!")
    print(f"{'=' * 70}")
    print(f"\n📁 All removed trades files saved in: {output_folder}/")
    
    return results


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    """
    Main entry point for comparing trades.
    
    You can choose to:
    1. Compare just RR=1 (single comparison)
    2. Compare all RR thresholds (multiple comparisons)
    """
    
    # Option 1: Compare only RR=1
    print("Running comparison for RR threshold = 1\n")
    removed_trades_rr1 = compare_and_extract_removed_trades(
        main_file="trades.csv",
        filtered_file="../version_2_Level_1_filtered_results/rr_threshold_1/final_result_rr_1.csv",
        output_file="removed_trades_rr_1.csv"
    )
    
    # Option 2: Uncomment below to compare ALL RR thresholds at once
    # print("\n\nRunning comparison for ALL RR thresholds\n")
    # all_removed = compare_multiple_rr_thresholds(
    #     main_file="trades.csv",
    #     base_folder="../version_2_Level_1_filtered_results",
    #     output_folder="removed_trades_analysis"
    # )