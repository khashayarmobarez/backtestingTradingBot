import pandas as pd
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
    
    Example:
        If rr_threshold = 2 and total_trades = 200:
        - Trade with R/R = 3.5 → adds +2 (the threshold value)
        - Trade with R/R = 1.8 → adds -1 (below threshold)
        - Trade with R/R = "SL" → adds -1 (stop loss hit)
        - Final score = raw_score - (200 / 10) = raw_score - 20
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
                # This ensures consistent scoring across different R/R levels
                score += rr_threshold
            else:
                # Loser: penalize by 1
                score -= 1
    
    # Apply trade count penalty: subtract (total_trades / 10)
    # This penalizes strategies with too many trades relative to their performance
    adjusted_score = score - (total_trades / 10)
    
    return adjusted_score


def calculate_max_losing_streak(trades_df, rr_threshold):
    """
    Find the longest consecutive losing streak in the trade list.
    
    A "losing trade" is defined as:
    - reward_risk < rr_threshold, OR
    - reward_risk == "SL" (Stop Loss)
    
    This metric helps identify the maximum drawdown potential or risk periods.
    A high losing streak indicates periods where the strategy underperformed.
    
    Args:
        trades_df (DataFrame): DataFrame containing trade data with 'reward_risk' column
        rr_threshold (int): The target reward/risk ratio we're evaluating against
    
    Returns:
        int: The maximum number of consecutive losing trades (0 if no losing streaks)
    
    Example:
        For trades: [WIN, LOSS, LOSS, LOSS, WIN, LOSS, WIN]
        The longest losing streak is 3
    """
    max_streak = 0       # Track the longest streak we've found
    current_streak = 0   # Track the current ongoing streak
    
    # Go through trades in order (chronologically)
    for rr in trades_df["reward_risk"]:
        # Check if this is a losing trade
        if rr == "SL":
            # Stop loss = losing trade
            current_streak += 1
        else:
            rr_value = float(rr)
            
            if rr_value < rr_threshold:
                # Below threshold = losing trade
                current_streak += 1
            else:
                # Winning trade: the streak is broken
                # Save the streak if it's the longest we've seen
                max_streak = max(max_streak, current_streak)
                # Reset the counter for the next potential streak
                current_streak = 0
    
    # Important: Check one last time after the loop ends
    # The longest streak might be at the end of the data
    max_streak = max(max_streak, current_streak)
    
    return max_streak


def calculate_quality_metric(net_score, max_losing_streak, total_trades):
    """
    Calculate the quality metric using a custom formula.
    
    Formula: (10 / max_losing_streak) * net_score
    
    Note: net_score is already adjusted for trade count (total_trades / 10 is subtracted in calculate_net_score)
    
    This metric combines:
    1. Risk assessment (via max_losing_streak) - inverted so lower streaks are better
    2. Net profitability (via net_score, already adjusted for trade frequency)
    
    Interpretation:
    - HIGHER values are BETTER (more positive)
    - Positive values indicate good performance relative to risk
    - Cannot be calculated if max_losing_streak <= 0 (division by zero/negative)
    
    Args:
        net_score (float): The calculated net score from calculate_net_score() (already adjusted)
        max_losing_streak (int): The longest losing streak from calculate_max_losing_streak()
        total_trades (int): Total number of trades in the dataset (not used in formula, already in net_score)
    
    Returns:
        float or None: The quality metric value, or None if max_losing_streak <= 0
    
    Example:
        net_score = 80 (already adjusted: 100 - 200/10)
        max_losing_streak = 5
        
        quality_metric = (10 / 5) * 80
                       = 2.0 * 80
                       = 160.0
    """
    # Edge case: cannot divide by zero or negative numbers
    if max_losing_streak <= 0:
        return None  # Return None to indicate this metric cannot be calculated
    
    # Apply the formula
    # Since net_score is already adjusted for (total_trades / 10), we just multiply
    quality_metric = (10 / max_losing_streak) * net_score
    
    return quality_metric


# ===============================================================
#  HELPER FUNCTIONS FOR FILE PROCESSING
# ===============================================================

def extract_rr_from_filename(filename):
    """
    Extract the R/R threshold value from a filename.
    
    Expected format: 'final_result_rr_2.csv' → extracts 2
    
    Args:
        filename (str): The filename to parse
    
    Returns:
        int or None: The R/R threshold value, or None if not found
    """
    match = re.search(r'rr_(\d+)', filename)
    if match:
        return int(match.group(1))
    return None


def extract_rr_from_folder(folder_name):
    """
    Extract the R/R threshold value from a folder name.
    
    Expected format: 'rr_threshold_2' → extracts 2
    
    Args:
        folder_name (str): The folder name to parse
    
    Returns:
        int or None: The R/R threshold value, or None if not found
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
       - max_losing_streak: Longest consecutive losing period
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
    
    Args:
        input_base_folder (str): Path to the folder containing R/R threshold subfolders
        output_file (str): Name of the output summary CSV file
    
    Returns:
        list: List of dictionaries containing all calculated metrics
    """
    
    # Print header
    print("=" * 70)
    print("  EXTRACTING METRICS FROM FILTERED RESULTS")
    print("=" * 70)
    print()
    
    # Initialize results storage
    results = []
    
    # Step 1: Iterate through all subdirectories in the base folder
    # sorted() ensures we process folders in order (rr_threshold_1, 2, 3, etc.)
    for folder_name in sorted(os.listdir(input_base_folder)):
        folder_path = os.path.join(input_base_folder, folder_name)
        
        # Skip if this is not a directory
        if not os.path.isdir(folder_path):
            continue
        
        # Step 2: Extract the R/R threshold from the folder name
        # Example: 'rr_threshold_2' → rr_threshold = 2
        rr_threshold = extract_rr_from_folder(folder_name)
        if rr_threshold is None:
            # Skip folders that don't match our naming pattern
            continue
        
        print(f"📊 Processing R/R Threshold: {rr_threshold}")
        
        # Step 3: Look for the final result file in this folder
        final_file = None
        for filename in os.listdir(folder_path):
            if filename.startswith("final_result_rr_") and filename.endswith(".csv"):
                final_file = filename
                break  # Stop searching once we find it
        
        # Check if we found a final result file
        if final_file is None:
            print(f"   ⚠️  No final result file found in {folder_name}")
            continue
        
        # Step 4: Load the CSV file into a pandas DataFrame
        file_path = os.path.join(folder_path, final_file)
        try:
            trades_df = pd.read_csv(file_path)
        except Exception as e:
            # Handle any errors reading the file
            print(f"   ❌ Error reading {final_file}: {e}")
            continue
        
        # Check if the file is empty
        if trades_df.empty:
            print(f"   ⚠️  Empty file: {final_file}")
            continue
        
        # Step 5: Calculate all three metrics
        total_trades = len(trades_df)
        
        # Metric 1: Net Score (adjusted for trade count)
        # Measures overall profitability vs the R/R threshold
        # Already includes the (total_trades / 10) penalty
        net_score = calculate_net_score(trades_df, rr_threshold, total_trades)
        
        # Metric 2: Max Losing Streak
        # Identifies the worst consecutive losing period
        max_losing_streak = calculate_max_losing_streak(trades_df, rr_threshold)
        
        # Metric 3: Quality Metric
        # Combines profitability and risk into a single number
        # net_score is already adjusted, so we don't pass total_trades again
        quality_metric = calculate_quality_metric(net_score, max_losing_streak, total_trades)
        
        # Step 6: Store the results for this R/R threshold
        results.append({
            "rr_threshold": rr_threshold,
            "net_score": net_score,
            "max_losing_streak": max_losing_streak,
            "total_trades": total_trades,
            "quality_metric": quality_metric,
            "file_path": file_path
        })
        
        # Step 7: Print individual results for this R/R threshold
        print(f"   ✅ Total Trades: {total_trades}")
        print(f"   ✅ Net Score: {net_score}")
        print(f"   ✅ Max Losing Streak: {max_losing_streak}")
        if quality_metric is not None:
            print(f"   ✅ Quality Metric: {quality_metric:.4f}")
        else:
            print(f"   ⚠️  Quality Metric: Cannot calculate (max_losing_streak <= 0)")
        print()
    
    # Step 8: Create and save summary report
    if results:
        # Convert list of dictionaries to a pandas DataFrame
        summary_df = pd.DataFrame(results)
        
        # Sort by R/R threshold for easier reading
        summary_df = summary_df.sort_values("rr_threshold")
        
        # Save the summary to a CSV file
        summary_df.to_csv(output_file, index=False)
        
        # Print completion message and summary table
        print("=" * 70)
        print("  ✅ METRICS EXTRACTION COMPLETE!")
        print("=" * 70)
        print(f"\n📋 Summary Report:")
        print(summary_df.to_string(index=False))
        print(f"\n💾 Summary saved to: {output_file}")
        
        # Step 9: Calculate and display additional statistics
        # Filter to only include rows where quality_metric could be calculated
        valid_metrics = summary_df[summary_df["quality_metric"].notna()]
        
        if not valid_metrics.empty:
            print(f"\n📊 Statistics:")
            
            # Find the best (maximum) quality metric
            # Remember: higher/more positive is better for this metric
            best_idx = valid_metrics['quality_metric'].idxmax()
            best_metric = valid_metrics.loc[best_idx, 'quality_metric']
            best_rr = valid_metrics.loc[best_idx, 'rr_threshold']
            print(f"   Best Quality Metric: {best_metric:.4f} (R/R = {best_rr})")
            
            # Find the worst (minimum) quality metric
            worst_idx = valid_metrics['quality_metric'].idxmin()
            worst_metric = valid_metrics.loc[worst_idx, 'quality_metric']
            worst_rr = valid_metrics.loc[worst_idx, 'rr_threshold']
            print(f"   Worst Quality Metric: {worst_metric:.4f} (R/R = {worst_rr})")
            
            # Calculate the average quality metric
            avg_metric = valid_metrics['quality_metric'].mean()
            print(f"   Average Quality Metric: {avg_metric:.4f}")
    else:
        # No results were found or processed
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