import pandas as pd
import numpy as np
import os
import re

# ===============================================================
#  METRIC CALCULATION FUNCTIONS
# ===============================================================

def calculate_net_score(trades_df, rr_threshold, total_trades):
    """
    Calculate the net score for a list of trades.
    
    This metric evaluates the overall quality of trades compared to a target R/R threshold.
    
    Scoring Rules:
    - If reward_risk > rr_threshold: Add +rr_threshold to score
    - If reward_risk <= rr_threshold: Subtract -1 from score
    - If reward_risk == "SL" (Stop Loss): Subtract -1 from score
    - Final adjustment: Subtract (total_trades / 10) from the score
    
    Args:
        trades_df (DataFrame): DataFrame containing trade data with 'reward_risk' column
        rr_threshold (int): The target reward/risk ratio we're evaluating against
        total_trades (int): Total number of trades (used for penalty calculation)
    
    Returns:
        float: The net score after applying trade count penalty
    """
    score = 0
    
    # Loop through each trade's reward/risk value
    for rr in trades_df["reward_risk"]:
        # Check if the trade hit stop loss
        if rr == "SL":
            score -= 1  # Penalize stop losses
        else:
            # Convert R/R to float for comparison
            rr_value = float(rr)
            
            # Check if this trade exceeded our threshold
            if rr_value > rr_threshold:
                # Winner: add the threshold value (not the actual R/R)
                score += rr_threshold
            else:
                # Loser: penalize by 1
                score -= 1
    
    # Apply trade count penalty
    adjusted_score = score - (total_trades / 10)
    
    return adjusted_score


def calculate_lowest_drawdown(trades_df, rr_threshold):
    """
    Calculate the absolute lowest drawdown for a given reward level.
    
    This function:
    1. Converts all reward_risk values to numeric (SL = 0)
    2. Applies the reward level: if R/R >= threshold → +threshold, else → -1
    3. Tests starting from every SL position
    4. Finds the absolute worst cumulative drawdown across all starting points
    
    A lower (more negative) drawdown indicates higher risk.
    
    Args:
        trades_df (DataFrame): DataFrame containing trade data with 'reward_risk' column
        rr_threshold (int): The reward level to test (from folder name)
    
    Returns:
        int: The absolute lowest drawdown value (typically negative)
    """
    
    # Convert reward_risk to handle both numeric and "SL"
    trades_df = trades_df.copy()
    trades_df["reward_risk"] = trades_df["reward_risk"].astype(str)
    
    def convert_to_numeric(rr):
        return 0.0 if rr == "SL" else float(rr)
    
    rr_values = trades_df["reward_risk"].apply(convert_to_numeric).values
    
    # Find all SL positions
    sl_positions = np.where(rr_values == 0)[0]
    
    # If no SL trades found, start from position 0
    if len(sl_positions) == 0:
        sl_positions = np.array([0])
    
    # Apply reward level transformation
    values = np.where(rr_values >= rr_threshold, rr_threshold, -1)
    
    absolute_lowest = float('inf')
    
    # Test starting from each SL position
    for start_idx in sl_positions:
        segment_values = values[start_idx:]
        segment_cumsum = np.cumsum(segment_values)
        lowest_in_this_run = np.min(np.minimum(segment_cumsum, 0))
        
        if lowest_in_this_run < absolute_lowest:
            absolute_lowest = lowest_in_this_run
    
    return int(absolute_lowest)


def calculate_quality_metric(net_score, lowest_drawdown, total_trades):
    """
    Calculate the quality metric using the lowest drawdown formula.
    
    Formula: (10 / abs(lowest_drawdown)) * net_score
    
    Note: net_score is already adjusted for trade count (total_trades / 10 is subtracted)
    
    This metric combines:
    1. Risk assessment (via lowest_drawdown) - inverted so lower drawdowns mean worse quality
    2. Net profitability (via net_score, already adjusted for trade frequency)
    
    The result will typically be negative since we're dividing by the absolute value
    of a negative drawdown and multiplying by an adjusted score.
    
    Interpretation:
    - HIGHER (less negative) values are BETTER
    - More negative values indicate worse performance relative to risk
    - Cannot be calculated if lowest_drawdown == 0 (division by zero)
    
    Args:
        net_score (float): The calculated net score from calculate_net_score() (already adjusted)
        lowest_drawdown (int): The absolute lowest drawdown (typically negative)
        total_trades (int): Total number of trades (not used in formula, already in net_score)
    
    Returns:
        float or None: The quality metric value, or None if lowest_drawdown == 0
    """
    # Edge case: cannot divide by zero
    if lowest_drawdown == 0:
        return None
    
    # Apply the formula using absolute value of drawdown
    quality_metric = (10 / abs(lowest_drawdown)) * net_score
    
    return quality_metric


# ===============================================================
#  HELPER FUNCTIONS FOR FILE PROCESSING
# ===============================================================

def extract_rr_from_filename(filename):
    """
    Extract the R/R threshold value from a filename.
    
    Expected format: 'final_result_rr_2.csv' → extracts 2
    """
    match = re.search(r'rr_(\d+)', filename)
    if match:
        return int(match.group(1))
    return None


def extract_rr_from_folder(folder_name):
    """
    Extract the R/R threshold value from a folder name.
    
    Expected format: 'rr_threshold_2' → extracts 2
    """
    match = re.search(r'rr_threshold_(\d+)', folder_name)
    if match:
        return int(match.group(1))
    return None


# ===============================================================
#  MAIN PROCESSING FUNCTION
# ===============================================================

def process_filtered_results(input_base_folder="level_1_filtered_results",
                             output_file="metrics_summary.csv"):
    """
    Process all filtered result files and extract performance metrics.
    
    This function:
    1. Scans through all R/R threshold folders
    2. Finds the final_result_rr_X.csv file in each folder
    3. Calculates three metrics for each dataset:
       - net_score: Overall performance score
       - lowest_drawdown: Absolute worst drawdown starting from any SL position
       - quality_metric: Combined quality assessment
    4. Creates a summary CSV with all metrics
    
    Expected folder structure:
        input_base_folder/
        ├── rr_threshold_1/
        │   └── final_result_rr_1.csv
        ├── rr_threshold_2/
        │   └── final_result_rr_2.csv
        └── rr_threshold_3/
            └── final_result_rr_3.csv
    """
    
    import time
    
    # Print header
    print("=" * 70)
    print("  EXTRACTING METRICS FROM FILTERED RESULTS")
    print("=" * 70)
    print()
    
    # Initialize results storage
    results = []
    
    # Get list of folders and count them
    all_folders = sorted(os.listdir(input_base_folder))
    total_folders = len(all_folders)
    processed_count = 0
    start_time = time.time()
    
    print(f"📁 Found {total_folders} folders to process\n")
    
    # Iterate through all subdirectories
    for folder_name in all_folders:
        folder_path = os.path.join(input_base_folder, folder_name)
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
        
        # Extract the R/R threshold from folder name
        rr_threshold = extract_rr_from_folder(folder_name)
        if rr_threshold is None:
            continue
        
        processed_count += 1
        elapsed_time = time.time() - start_time
        avg_time_per_folder = elapsed_time / processed_count
        remaining_folders = total_folders - processed_count
        estimated_remaining = avg_time_per_folder * remaining_folders
        
        print(f"📊 [{processed_count}/{total_folders}] Processing R/R Threshold: {rr_threshold}")
        print(f"   ⏱️  Elapsed: {elapsed_time:.1f}s | Avg: {avg_time_per_folder:.2f}s/folder | ETA: {estimated_remaining:.1f}s")
        
        # Look for the final result file
        final_file = None
        for filename in os.listdir(folder_path):
            if filename.startswith("final_result_rr_") and filename.endswith(".csv"):
                final_file = filename
                break
        
        if final_file is None:
            print(f"   ⚠️  No final result file found in {folder_name}")
            continue
        
        # Load the CSV file
        file_path = os.path.join(folder_path, final_file)
        try:
            trades_df = pd.read_csv(file_path)
        except Exception as e:
            print(f"   ❌ Error reading {final_file}: {e}")
            continue
        
        if trades_df.empty:
            print(f"   ⚠️  Empty file: {final_file}")
            continue
        
        # Calculate all three metrics
        total_trades = len(trades_df)
        
        # Metric 1: Net Score (adjusted for trade count)
        net_score = calculate_net_score(trades_df, rr_threshold, total_trades)
        
        # Metric 2: Lowest Drawdown (replaces max losing streak)
        lowest_drawdown = calculate_lowest_drawdown(trades_df, rr_threshold)
        
        # Metric 3: Quality Metric
        quality_metric = calculate_quality_metric(net_score, lowest_drawdown, total_trades)
        
        # Store the results
        results.append({
            "rr_threshold": rr_threshold,
            "net_score": net_score,
            "lowest_drawdown": lowest_drawdown,
            "total_trades": total_trades,
            "quality_metric": quality_metric,
            "file_path": file_path
        })
        
        # Print individual results
        quality_str = f"{quality_metric:.4f}" if quality_metric is not None else "N/A"
        print(f"   ✅ Trades: {total_trades} | Net: {net_score:.1f} | Drawdown: {lowest_drawdown} | Quality: {quality_str}\n")
    
    # Create and save summary report
    if results:
        total_time = time.time() - start_time
        
        summary_df = pd.DataFrame(results)
        summary_df = summary_df.sort_values("rr_threshold")
        summary_df.to_csv(output_file, index=False)
        
        print("=" * 70)
        print("  ✅ METRICS EXTRACTION COMPLETE!")
        print("=" * 70)
        print(f"\n⏱️  Total Processing Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"📊 Processed {len(results)} folders successfully")
        print(f"\n📋 Summary Report:")
        print(summary_df.to_string(index=False))
        print(f"\n💾 Summary saved to: {output_file}")
        
        # Calculate statistics
        valid_metrics = summary_df[summary_df["quality_metric"].notna()]
        
        if not valid_metrics.empty:
            print(f"\n📊 Statistics:")
            
            # Best (highest/least negative) quality metric
            best_idx = valid_metrics['quality_metric'].idxmax()
            best_metric = valid_metrics.loc[best_idx, 'quality_metric']
            best_rr = valid_metrics.loc[best_idx, 'rr_threshold']
            print(f"   Best Quality Metric: {best_metric:.4f} (R/R = {best_rr})")
            
            # Worst (lowest/most negative) quality metric
            worst_idx = valid_metrics['quality_metric'].idxmin()
            worst_metric = valid_metrics.loc[worst_idx, 'quality_metric']
            worst_rr = valid_metrics.loc[worst_idx, 'rr_threshold']
            print(f"   Worst Quality Metric: {worst_metric:.4f} (R/R = {worst_rr})")
            
            # Average quality metric
            avg_metric = valid_metrics['quality_metric'].mean()
            print(f"   Average Quality Metric: {avg_metric:.4f}")
    else:
        print("❌ No results found to process!")
    
    return results


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    """
    Main entry point when running this script directly.
    
    Modify the parameters below to match your folder structure:
    - input_base_folder: Path to the folder containing rr_threshold_X subfolders
    - output_file: Name for the summary CSV that will be created
    """
    process_filtered_results(
        input_base_folder="../version_2_Level_1_filtered_results",
        output_file="metrics_summary.csv"
    )