import pandas as pd
import numpy as np
import time
import boto3

# ===============================================================
#  S3 CLIENT (LIARA BUCKET)
# ===============================================================

s3 = boto3.client(
    "s3",
    endpoint_url="https://storage.c2.liara.space",
    aws_access_key_id="YOUR_ACCESS_KEY",     # 
    aws_secret_access_key="YOUR_SECRET_KEY", # 
)

BUCKET_NAME = "janyar"


# ===============================================================
#  OPTIMIZED LOWEST DRAWDOWN - CLEAN LOG VERSION
# ===============================================================

def calculate_lowest_drawdown(input_csv="trades.csv", output_csv="lowest_drawdown_results.csv"):
    """
    Optimized version using NumPy vectorization.
    - Tests from every SL position.
    - Prints only final results (no progress logs).
    """

    start_time = time.time()

    # Load the trades CSV
    try:
        trades = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"❌ Error: {input_csv} not found!")
        return

    # Convert reward_risk to handle both numeric and "SL"
    trades["reward_risk"] = trades["reward_risk"].astype(str)

    def convert_to_numeric(rr):
        return 0.0 if rr == "SL" else float(rr)

    rr_values = trades["reward_risk"].apply(convert_to_numeric).values
    n_trades = len(rr_values)

    # Find all SL positions
    sl_positions = np.where(rr_values == 0)[0]
    if len(sl_positions) == 0:
        print("❌ No SL trades found in the list!")
        return

    # Determine reward levels to test
    max_reward = int(np.max(rr_values))
    reward_levels = list(range(1, max_reward + 1))

    results = []

    # Test each reward level
    for reward_level in reward_levels:
        values = np.where(rr_values >= reward_level, reward_level, -1)
        absolute_lowest = float('inf')
        best_starting_position = None

        # Test starting from each SL position
        for start_idx in sl_positions:
            segment_values = values[start_idx:]
            segment_cumsum = np.cumsum(segment_values)
            lowest_in_this_run = np.min(np.minimum(segment_cumsum, 0))

            if lowest_in_this_run < absolute_lowest:
                absolute_lowest = lowest_in_this_run
                best_starting_position = int(start_idx)

        reward_time = time.time() - start_time
        print(f"✅ Reward Level {reward_level}: Lowest={absolute_lowest}, StartIndex={best_starting_position}")

        results.append({
            "Reward_Level": reward_level,
            "Absolute_Lowest": int(absolute_lowest),
            "Starting_Position": best_starting_position,
            "Calculation_Time_Seconds": round(reward_time, 2)
        })

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # ===============================================================
    #  SAVE LOCALLY + UPLOAD TO LIARA BUCKET
    # ===============================================================

    # Save locally first
    results_df.to_csv(output_csv, index=False)

    # Upload to bucket
    s3.upload_file(
        Filename=output_csv,
        Bucket=BUCKET_NAME,
        Key=output_csv  # file inside bucket
    )

    print(f"\n📤 Uploaded to bucket '{BUCKET_NAME}' as '{output_csv}'")

    total_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS - LOWEST DRAWDOWN BY REWARD LEVEL")
    print("=" * 70)
    print(results_df.to_string(index=False))
    print(f"\n💾 Results saved locally as: {output_csv}")
    print(f"📥 And uploaded to bucket: {output_csv}")
    print(f"⏱️ Total execution time: {total_time:.2f} seconds\n")

    return results_df


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LOWEST DRAWDOWN CALCULATOR (CLEAN LOG VERSION)")
    print("=" * 70)
    print()

    # Run main function
    results = calculate_lowest_drawdown(
        input_csv="trades.csv",
        output_csv="lowest_drawdown_results.csv"
    )

    print("=" * 70)
    print("  COMPLETE!")
    print("=" * 70)
