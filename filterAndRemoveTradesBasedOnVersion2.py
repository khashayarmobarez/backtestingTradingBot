import pandas as pd
import os
import math
from collections import defaultdict

def extract_reward_risks(trades_df):
    """
    Extract all unique R/R values from the dataframe and round them down.
    SL entries are treated as 0 (but will count as -1 in scoring).
    """
    rr_values = []
    for rr in trades_df["reward_risk"].unique():
        if rr != "SL":
            rr_values.append(math.floor(float(rr)))
    
    return sorted(list(set(rr_values)))


def calculate_list_score(trades_df, rr_threshold):
    """
    Calculate the score for a list of trades based on R/R threshold.
    
    Rules:
    - If reward_risk > rr_threshold: +rr_threshold
    - If reward_risk < rr_threshold or reward_risk == "SL": -1
    - Penalty: -1 for every 20 trades
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


def filter_by_distance(input_folder, rr_threshold, output_folder):
    """
    Step 1: Filter CSV files by R/R threshold at distance level.
    Returns list of files that pass the filter.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    passed_files = []
    
    # Process each CSV file in the input folder
    for filename in os.listdir(input_folder):
        if not filename.endswith('.csv') or filename == 'summary_report.csv':
            continue
        
        filepath = os.path.join(input_folder, filename)
        trades_df = pd.read_csv(filepath)
        
        # Calculate score
        score = calculate_list_score(trades_df, rr_threshold)
        
        if score > 0:
            # Save the file to output folder
            output_path = os.path.join(output_folder, filename)
            trades_df.to_csv(output_path, index=False)
            passed_files.append(filename)
            print(f"   ✓ {filename}: Score = {score} (PASSED)")
        else:
            print(f"   ✗ {filename}: Score = {score} (FILTERED OUT)")
    
    return passed_files


def filter_by_hour(input_folder, rr_threshold, output_folder):
    """
    Step 2: Categorize by hour and filter each hour-based list.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    passed_trades = []
    
    # Process each file from the previous step
    for filename in os.listdir(input_folder):
        if not filename.endswith('.csv'):
            continue
        
        filepath = os.path.join(input_folder, filename)
        trades_df = pd.read_csv(filepath)
        
        # Extract hour from time column
        trades_df["hour"] = trades_df["time"].apply(lambda x: x.split(":")[0])
        
        # Get unique hours
        unique_hours = sorted(trades_df["hour"].unique())
        
        print(f"\n   Processing {filename}:")
        
        # Filter by each hour
        for hour in unique_hours:
            hour_trades = trades_df[trades_df["hour"] == hour].copy()
            score = calculate_list_score(hour_trades, rr_threshold)
            
            if score > 0:
                passed_trades.append(hour_trades)
                print(f"      ✓ Hour {hour}: Score = {score} (PASSED)")
            else:
                print(f"      ✗ Hour {hour}: Score = {score} (FILTERED OUT)")
    
    # Combine all passed trades
    if passed_trades:
        combined_df = pd.concat(passed_trades, ignore_index=True)
        combined_df = combined_df.drop(columns=["hour"])  # Remove temporary hour column
        return combined_df
    else:
        return pd.DataFrame()


def filter_by_weekday(trades_df, rr_threshold):
    """
    Step 3: Categorize by weekday and filter each weekday-based list.
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    passed_trades = []
    
    # Get unique weekdays
    unique_days = trades_df["day_of_week"].unique()
    
    print(f"\n   Filtering by weekday:")
    
    # Filter by each weekday
    for day in unique_days:
        day_trades = trades_df[trades_df["day_of_week"] == day].copy()
        score = calculate_list_score(day_trades, rr_threshold)
        
        if score > 0:
            passed_trades.append(day_trades)
            print(f"      ✓ {day}: Score = {score} (PASSED)")
        else:
            print(f"      ✗ {day}: Score = {score} (FILTERED OUT)")
    
    # Combine all passed trades and sort by date and time
    if passed_trades:
        combined_df = pd.concat(passed_trades, ignore_index=True)
        combined_df = combined_df.sort_values(by=["date", "time"])
        return combined_df
    else:
        return pd.DataFrame()


def level_1_filtering(input_folder="categorized_by_distance_results", 
                      output_base_folder="level_1_filtered_results"):
    """
    Main function that performs the complete Level 1 filtering process.
    Creates separate output folders for each R/R threshold.
    """
    
    print("=" * 70)
    print("  LEVEL 1 FILTERING - REWARD/RISK BASED CATEGORIZATION")
    print("=" * 70)
    print()
    
    # Step 1: Extract all unique R/R values from all files
    print("📊 Step 1: Extracting all available R/R values...")
    all_rr_values = set()
    
    for filename in os.listdir(input_folder):
        if not filename.endswith('.csv') or filename == 'summary_report.csv':
            continue
        
        filepath = os.path.join(input_folder, filename)
        trades_df = pd.read_csv(filepath)
        rr_values = extract_reward_risks(trades_df)
        all_rr_values.update(rr_values)
    
    all_rr_values = sorted(list(all_rr_values))
    print(f"✅ Found R/R thresholds: {all_rr_values}\n")
    
    # Process each R/R threshold
    for rr_threshold in all_rr_values:
        print("=" * 70)
        print(f"🎯 Processing R/R Threshold: {rr_threshold}")
        print("=" * 70)
        
        # Create output folder for this R/R threshold
        rr_output_folder = os.path.join(output_base_folder, f"rr_threshold_{rr_threshold}")
        
        # Step 2: Filter by distance
        print(f"\n📂 Step 2.1: Filtering by distance (R/R = {rr_threshold})...")
        distance_output = os.path.join(rr_output_folder, "step_1_distance_filtered")
        passed_files = filter_by_distance(input_folder, rr_threshold, distance_output)
        
        if not passed_files:
            print(f"\n❌ No files passed the distance filter for R/R = {rr_threshold}")
            continue
        
        print(f"\n✅ {len(passed_files)} files passed distance filtering")
        
        # Step 3: Filter by hour
        print(f"\n⏰ Step 2.2: Filtering by hour (R/R = {rr_threshold})...")
        hour_filtered_df = filter_by_hour(distance_output, rr_threshold, 
                                          os.path.join(rr_output_folder, "step_2_hour_filtered"))
        
        if hour_filtered_df.empty:
            print(f"\n❌ No trades passed the hour filter for R/R = {rr_threshold}")
            continue
        
        print(f"\n✅ {len(hour_filtered_df)} trades passed hour filtering")
        
        # Step 4: Filter by weekday
        print(f"\n📅 Step 2.3: Filtering by weekday (R/R = {rr_threshold})...")
        final_df = filter_by_weekday(hour_filtered_df, rr_threshold)
        
        if final_df.empty:
            print(f"\n❌ No trades passed the weekday filter for R/R = {rr_threshold}")
            continue
        
        # Save final result
        final_output_path = os.path.join(rr_output_folder, f"final_result_rr_{rr_threshold}.csv")
        final_df.to_csv(final_output_path, index=False)
        
        print(f"\n✅ {len(final_df)} trades in final result for R/R = {rr_threshold}")
        print(f"💾 Saved to: {final_output_path}")
        print()
    
    print("\n" + "=" * 70)
    print("  ✅ LEVEL 1 FILTERING COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Results saved in: {output_base_folder}/")
    print("📊 Check each rr_threshold_X folder for results")


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    level_1_filtering(
        input_folder="categorized_by_distance_results",
        output_base_folder="level_1_filtered_results"
    )