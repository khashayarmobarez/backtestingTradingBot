import pandas as pd
import os
import shutil

# ===============================================================
#  FILTER LISTS BASED ON PROFITABILITY FORMULA
# ===============================================================

def apply_profitability_formula(trades_df):
    """
    Applies the profitability formula to determine if a list should be kept.
    
    Formula for each TP (in order):
    (TP_value × remaining_TPs) - total_SLs
    
    If ANY result > 0, the list is successful.
    If ALL results ≤ 0, the list fails.
    
    Returns: (is_successful, calculations_log)
    """
    
    # Convert reward_risk to string first to handle comparison
    trades_df["reward_risk"] = trades_df["reward_risk"].astype(str)
    
    # Extract numeric R/R values (TPs) - ignore "SL"
    # Filter out "SL" and convert to float
    tps = trades_df[trades_df["reward_risk"] != "SL"]["reward_risk"].apply(lambda x: float(x)).tolist()
    
    # Count total SL trades
    initial_sl_count = len(trades_df[trades_df["reward_risk"] == "SL"])
    
    # If no TPs at all, fail immediately
    if len(tps) == 0:
        return False, ["No TPs found - All trades are SL"]
    
    # Track calculations
    calculations = []
    current_sl_count = initial_sl_count
    
    # Iterate through each TP
    for i, tp_value in enumerate(tps):
        remaining_tps = len(tps) - i
        
        # Apply formula: (TP × remaining_TPs) - total_SLs
        result = (tp_value * remaining_tps) - current_sl_count
        
        calculation_log = f"Step {i+1}: ({tp_value} × {remaining_tps}) - {current_sl_count} = {result:.2f}"
        calculations.append(calculation_log)
        
        # If result > 0, the list is successful
        if result > 0:
            calculations.append(f"✅ PASS - Result {result:.2f} > 0")
            return True, calculations
        
        # Otherwise, count this TP as SL for next iteration
        current_sl_count += 1
    
    # If we went through all TPs and no result > 0, fail
    calculations.append(f"❌ FAIL - All results ≤ 0")
    return False, calculations


def filter_successful_lists(input_folder, output_folder=None, show_details=False):
    """
    Filters trading lists based on profitability formula.
    Only copies lists that pass the formula to the output folder.
    
    Parameters:
    - input_folder: Folder containing categorized CSV files
    - output_folder: Where to save successful lists (default: {input_folder}_filtered)
    - show_details: If True, prints detailed calculations for each file
    """
    
    # Set default output folder name
    if output_folder is None:
        output_folder = f"{input_folder}_filtered"
    
    # Create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created folder: {output_folder}/\n")
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"❌ Error: Folder '{input_folder}' not found!")
        return
    
    # Get all CSV files from input folder
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    
    if len(csv_files) == 0:
        print(f"❌ No CSV files found in '{input_folder}'")
        return
    
    print(f"📂 Processing {len(csv_files)} files from '{input_folder}/'...\n")
    
    # Track statistics
    passed_files = []
    failed_files = []
    skipped_files = []
    
    # Process each CSV file
    for filename in csv_files:
        filepath = os.path.join(input_folder, filename)
        
        # Skip summary reports
        if "summary" in filename.lower():
            skipped_files.append(filename)
            continue
        
        try:
            # Load the CSV
            df = pd.read_csv(filepath)
            
            # Skip empty files
            if len(df) == 0:
                print(f"⚠️  SKIPPED: {filename} (empty file)")
                skipped_files.append(filename)
                continue
            
            # Apply the formula
            is_successful, calculations = apply_profitability_formula(df)
            
            if is_successful:
                # Copy file to output folder
                output_path = os.path.join(output_folder, filename)
                shutil.copy2(filepath, output_path)
                passed_files.append(filename)
                print(f"✅ PASS: {filename} ({len(df)} trades)")
                
                if show_details:
                    for calc in calculations:
                        print(f"     {calc}")
                    print()
            else:
                failed_files.append(filename)
                print(f"❌ FAIL: {filename} ({len(df)} trades)")
                
                if show_details:
                    for calc in calculations:
                        print(f"     {calc}")
                    print()
        
        except Exception as e:
            print(f"⚠️  ERROR processing {filename}: {str(e)}")
            skipped_files.append(filename)
    
    # Print summary
    print("\n" + "=" * 60)
    print("  FILTERING SUMMARY")
    print("=" * 60)
    print(f"Total Files Processed: {len(csv_files)}")
    print(f"✅ Passed (Copied): {len(passed_files)}")
    print(f"❌ Failed (Not Copied): {len(failed_files)}")
    print(f"⚠️  Skipped: {len(skipped_files)}")
    print("=" * 60)
    
    if len(passed_files) > 0:
        print(f"\n📂 Successful lists saved to: {output_folder}/")
        print("\nPassed files:")
        for f in passed_files:
            print(f"  • {f}")
    
    if len(failed_files) > 0:
        print(f"\n❌ Failed files (not copied):")
        for f in failed_files:
            print(f"  • {f}")
    
    # Create a summary report
    create_filter_summary(passed_files, failed_files, skipped_files, output_folder)


def create_filter_summary(passed, failed, skipped, output_folder):
    """
    Creates a summary report of the filtering process.
    """
    summary_data = {
        "Status": ["Passed"] * len(passed) + ["Failed"] * len(failed) + ["Skipped"] * len(skipped),
        "Filename": passed + failed + skipped
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = os.path.join(output_folder, "filter_summary.csv")
    summary_df.to_csv(summary_file, index=False)
    
    print(f"\n💾 Filter summary saved to: {summary_file}")


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  PROFITABILITY FILTER - SUCCESSFUL LISTS ONLY")
    print("=" * 60)
    print()
    
    # Example usage - you can change these parameters:
    
    # For categorized by distance:
    filter_successful_lists(
        input_folder="categorized_by_hour",
        output_folder="categorized_by_hour_filtered",
        show_details=False  # Set to True to see detailed calculations
    )
    
    # Uncomment to also filter other categorizations:
    
    # filter_successful_lists(
    #     input_folder="categorized_by_day",
    #     output_folder="categorized_by_day_filtered",
    #     show_details=False
    # )
    
    # filter_successful_lists(
    #     input_folder="categorized_by_hour",
    #     output_folder="categorized_by_hour_filtered",
    #     show_details=False
    # )
    
    print("\n" + "=" * 60)
    print("  Filtering complete!")
    print("=" * 60)