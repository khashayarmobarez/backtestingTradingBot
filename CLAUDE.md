# Trading Backtesting Analysis System

## Overview

A Python-based backtesting analysis pipeline that processes historical trading data, categorizes trades by multiple dimensions, applies profitability filters, and calculates drawdown metrics. The system uses a multi-level filtering approach to identify optimal trading strategies based on reward/risk ratios.

## System Architecture

### Core Components

1. **Data Processing Pipeline**
   - Trade categorization by distance, weekday, and hour
   - Multi-level filtering based on profitability formulas
   - Drawdown calculation and optimization

2. **Storage Integration**
   - S3-compatible storage (Liara) for result persistence
   - Local CSV-based intermediate processing
   - Automated upload of final results

3. **Analysis Modules**
   - Profitability scoring algorithms
   - Statistical metrics extraction
   - Performance quality assessment

## Data Flow

```
trades.csv (input)
    ↓
Categorization Layer (parallel processing)
    ├─→ categorize_by_distance.py → categorized_by_distance_results/
    ├─→ categorize_by_weekdays.py → categorized_by_day/
    └─→ categorize_by_hour.py → categorized_by_hour/
    ↓
Filtering Layer
    ├─→ filter_successful_lists.py → *_filtered/
    └─→ filterAndRemoveTradesBasedOnVersion2.py → level_1_filtered_results/
    ↓
Analysis Layer
    ├─→ extract_metrics.py → metrics_summary.csv
    ├─→ calculate_all_formula.py → formula_results.csv
    └─→ calculate_lowest_drawdown.py → lowest_drawdown_results.csv
    ↓
Cloud Storage (S3/Liara)
```

## Module Documentation

### 1. Trade Categorization

#### `categorize_by_distance.py`
Separates trades into Buy/Sell groups and organizes by distance value (rounded down to nearest integer).

**Input:** `trades.csv`  
**Output:** Multiple CSV files in `categorized_by_distance_results/`  
**Naming:** `{buy|sell}_distance_{value}.csv`

**Key Features:**
- Rounds distance to 1 decimal place, then floors to integer
- Sorts by reward/risk (ascending, SL trades at end)
- Generates summary report with statistics

#### `categorize_by_weekdays.py`
Groups trades by day of week while maintaining Buy/Sell separation.

**Input:** `trades.csv`  
**Output:** Multiple CSV files in `categorized_by_day/`  
**Naming:** `{buy|sell}_{monday|tuesday|...}.csv`

**Key Features:**
- Preserves proper weekday ordering (Monday → Sunday)
- Calculates average R/R, profit, and distance per day
- Filters out days with no trades

#### `categorize_by_hour.py`
Organizes trades by hour of execution time.

**Input:** `trades.csv`  
**Output:** Multiple CSV files in `categorized_by_hour/`  
**Naming:** `{buy|sell}_hour_{HH}.csv`

**Key Features:**
- Extracts hour from time column (format: HH:MM:SS)
- Maintains chronological sorting within each hour
- Summary includes hourly performance metrics

### 2. Filtering System

#### `filter_successful_lists.py`
Applies profitability formula to identify successful trading sequences.

**Profitability Formula:**
```
For each TP (in ascending order):
  (TP_value × remaining_TPs) - total_SLs

If ANY result > 0: List passes
If ALL results ≤ 0: List fails
```

**Input:** Any categorized folder  
**Output:** `{input_folder}_filtered/`

**Process:**
1. Convert all R/R values to numeric (SL → excluded from TP list)
2. Sort TPs ascending
3. Iterate through TPs, counting each as SL after evaluation
4. Pass if any calculation yields positive result

**Features:**
- Detailed calculation logs (optional via `show_details`)
- Filter summary CSV generation
- Skips summary reports automatically

#### `filterAndRemoveTradesBasedOnVersion2.py`
Multi-level filtering system with R/R threshold-based scoring.

**Scoring Formula:**
```
For each trade:
  if R/R > threshold: +threshold
  if R/R ≤ threshold or SL: -1

Penalty: -floor(trade_count / 20)
```

**Process:**
1. **Level 1 (Distance):** Filter by R/R threshold at distance level
2. **Level 2 (Hour):** Re-categorize passing trades by hour, filter again
3. **Level 3 (Weekday):** Re-categorize by weekday, final filter

**Output Structure:**
```
level_1_filtered_results/
├── rr_threshold_1/
│   ├── step_1_distance_filtered/
│   ├── step_2_hour_filtered/
│   └── final_result_rr_1.csv
├── rr_threshold_2/
│   └── ...
└── rr_threshold_N/
```

**Key Features:**
- Extracts all unique R/R values from dataset automatically
- Processes each R/R threshold independently
- Maintains chronological order in final results
- Skips thresholds with no passing trades

### 3. Analysis & Metrics

#### `extract_metrics.py`
Calculates comprehensive performance metrics for filtered results.

**Metrics:**

1. **Net Score**
   ```
   For each trade:
     if R/R > threshold: +threshold
     else: -1
   
   Adjusted Score = raw_score - (total_trades / 10)
   ```

2. **Max Losing Streak**
   - Longest consecutive sequence of trades where R/R < threshold or SL
   - Used for risk assessment

3. **Quality Metric**
   ```
   quality_metric = (10 / max_losing_streak) × net_score
   ```
   - Combines profitability and risk
   - Higher values indicate better performance
   - Cannot calculate if max_losing_streak ≤ 0

**Input:** `level_1_filtered_results/` (expects subfolder structure)  
**Output:** `metrics_summary.csv`

**Summary Statistics:**
- Best/worst quality metric across all R/R thresholds
- Average quality metric
- Individual metrics per threshold

#### `calculate_all_formula.py`
Applies profitability formula to entire dataset without filtering.

**Input:** `trades.csv`  
**Output:** 
- `formula_results.csv` (structured data)
- `formula_report.txt` (human-readable report)

**Features:**
- Sorts TPs ascending before calculation
- Shows all calculation steps
- Identifies positive vs negative results
- Summary statistics on result distribution

#### `calculate_lowest_drawdown.py`
Optimized NumPy-based drawdown calculation.

**Algorithm:**
```
For each reward_level (1 to max_R/R):
  Convert trades: R/R ≥ level → +level, else → -1
  
  For each SL position as starting point:
    Calculate cumulative sum from start
    Find minimum (most negative) point
  
  Record absolute lowest across all start positions
```

**Input:** `trades.csv`  
**Output:** `lowest_drawdown_results.csv`

**Columns:**
- `Reward_Level`: Target R/R threshold
- `Absolute_Lowest`: Worst drawdown from optimal start
- `Starting_Position`: Index of best starting trade
- `Calculation_Time_Seconds`: Performance metric

**Optimization:**
- Vectorized NumPy operations
- Tests only from SL positions (natural restart points)
- Progress logging per reward level

#### `main.py`
Primary entry point with cloud storage integration.

**Features:**
- Wraps `calculate_lowest_drawdown()` functionality
- Uploads results to S3-compatible bucket (Liara)
- Boto3 client configuration for custom endpoint
- Clean logging (final results only, no progress spam)

**S3 Configuration:**
```python
endpoint_url: "https://storage.c2.liara.space"
bucket: "janyar"
```

## Data Schema

### Input Schema: `trades.csv`

Required columns:
- `type`: "Buy" | "Sell"
- `date`: Date string
- `time`: "HH:MM:SS" format
- `day_of_week`: Full weekday name
- `distance`: Numeric value
- `reward_risk`: Numeric value or "SL"
- `max_profit`: Numeric value

Optional columns (used in analysis):
- Any additional metrics or identifiers

### Intermediate Files

All categorized CSVs maintain the same schema as input with potential additions:
- `distance_rounded`: Integer (in distance categorization)
- `hour`: "HH" string (in hour categorization)

### Output Schemas

**metrics_summary.csv:**
- `rr_threshold`: Integer
- `net_score`: Float
- `max_losing_streak`: Integer
- `total_trades`: Integer
- `quality_metric`: Float | None
- `file_path`: String

**formula_results.csv:**
- `Step`: Integer
- `TP_Value`: Float
- `Remaining_TPs`: Integer
- `Total_SLs`: Integer
- `Formula`: String (human-readable)
- `Result`: Float
- `Status`: "✅ Positive" | "❌ Negative/Zero"

**lowest_drawdown_results.csv:**
- `Reward_Level`: Integer
- `Absolute_Lowest`: Integer (negative value)
- `Starting_Position`: Integer (index)
- `Calculation_Time_Seconds`: Float

## Dependencies

```
pandas >= 2.0.0
numpy >= 1.24.0
matplotlib >= 3.7.0
boto3 (for S3/cloud storage)
```

## Configuration

### S3 Storage (main.py)
Update credentials in `main.py`:
```python
s3 = boto3.client(
    "s3",
    endpoint_url="https://storage.c2.liara.space",
    aws_access_key_id="YOUR_ACCESS_KEY",
    aws_secret_access_key="YOUR_SECRET_KEY",
)
BUCKET_NAME = "your-bucket-name"
```

### File Paths
Modify input/output paths in `__main__` sections of each module:
```python
categorize_trades(
    input_csv="custom_input.csv",
    output_folder="custom_output"
)
```

## Usage Workflows

### Workflow 1: Basic Categorization
```bash
python categorize_by_distance.py
python categorize_by_weekdays.py
python categorize_by_hour.py
```

### Workflow 2: Simple Filtering
```bash
python categorize_by_hour.py
python filter_successful_lists.py
```

### Workflow 3: Multi-Level Analysis
```bash
python categorize_by_distance.py
python filterAndRemoveTradesBasedOnVersion2.py
python extract_metrics.py
```

### Workflow 4: Complete Pipeline
```bash
# 1. Categorize
python categorize_by_distance.py

# 2. Multi-level filter
python filterAndRemoveTradesBasedOnVersion2.py

# 3. Extract metrics
python extract_metrics.py

# 4. Calculate drawdown
python main.py

# 5. Optional: Full formula analysis
python calculate_all_formula.py
```

## Algorithm Details

### Reward/Risk Sorting
All categorization modules use consistent sorting:
1. Separate numeric R/R from "SL" trades
2. Sort numeric trades ascending by R/R value
3. Concatenate: numeric first, SL trades last

**Implementation:**
```python
def sort_by_reward_risk(df):
    numeric_trades = df[df["reward_risk"] != "SL"].copy()
    sl_trades = df[df["reward_risk"] == "SL"].copy()
    numeric_trades = numeric_trades.sort_values("reward_risk", ascending=True)
    return pd.concat([numeric_trades, sl_trades], ignore_index=True)
```

### Profitability Formula Logic
The formula simulates consuming TPs in order while tracking SLs:

```python
current_sl_count = initial_sl_count

for i, tp_value in enumerate(sorted_tps):
    remaining_tps = len(tps) - i
    result = (tp_value × remaining_tps) - current_sl_count
    
    if result > 0:
        return True  # List is profitable
    
    current_sl_count += 1  # Treat this TP as SL for next iteration

return False  # No profitable configuration found
```

**Rationale:**
- Tests if any TP threshold can overcome accumulated losses
- Each TP becomes a "potential SL" for subsequent thresholds
- Prioritizes lower TPs (more conservative strategy)

### Quality Metric Interpretation
```
quality_metric = (10 / max_losing_streak) × net_score
```

**Components:**
- **Risk Factor (10 / streak):** Inverse relationship—shorter streaks are better
- **Net Score:** Already penalized for high trade volume
- **Combined:** Balances profitability against risk exposure

**Comparison:**
- Positive values: Strategy worth considering
- Higher values: Better risk-adjusted performance
- Negative values: Strategy underperforms relative to risk
- Cannot calculate if no losing streaks exist (division by zero)

### Drawdown Optimization Strategy
Why test from SL positions only?

1. **Natural Reset Points:** SL trades represent strategy failures and logical restart points
2. **Performance:** Reduces search space from O(n²) to O(n × m) where m = SL count
3. **Practical Relevance:** Real traders often re-evaluate after stop losses

**Vectorization Benefits:**
- NumPy cumsum replaces Python loops
- Eliminates incremental updates
- 10-100× faster than iterative approach

## Performance Characteristics

### Time Complexity
- **Categorization:** O(n log n) per category (dominated by sorting)
- **Filtering:** O(n × k) where k = number of categories
- **Drawdown:** O(n × m × r) where m = SL count, r = max reward level
- **Metrics:** O(n) per filtered result

### Memory Usage
- **Categorization:** O(n) for data duplication across files
- **Multi-level filtering:** O(n × r) for r thresholds
- **Drawdown:** O(n) due to NumPy arrays (vectorized operations)

### Bottlenecks
1. **File I/O:** Writing multiple CSV files in categorization
2. **Drawdown calculation:** Testing multiple reward levels (mitigated by vectorization)
3. **Multi-level filtering:** Iterating through all R/R thresholds

## Error Handling

### Missing Files
All modules check for `trades.csv` existence:
```python
try:
    trades = pd.read_csv(input_csv)
except FileNotFoundError:
    print(f"❌ Error: {input_csv} not found!")
    return
```

### Empty DataFrames
Filtering functions check for empty results:
```python
if final_df.empty:
    print(f"❌ No trades passed filter")
    continue
```

### Division by Zero
Quality metric handles zero/negative losing streaks:
```python
if max_losing_streak <= 0:
    return None
```

### Invalid Reward/Risk Values
Conversion handles both numeric and "SL":
```python
def convert_to_numeric(rr):
    return 0.0 if rr == "SL" else float(rr)
```

## Future Enhancements

### Potential Improvements
1. **Parallel Processing:** Use multiprocessing for categorization
2. **Database Backend:** Replace CSV with SQLite/PostgreSQL
3. **Incremental Updates:** Process only new trades, not full dataset
4. **Interactive Dashboard:** Streamlit/Dash for result visualization
5. **Backtesting Validation:** Walk-forward analysis and out-of-sample testing
6. **Advanced Metrics:** Sharpe ratio, Sortino ratio, max drawdown duration
7. **Strategy Optimization:** Genetic algorithms for parameter tuning

### Code Quality
1. **Type Hints:** Add throughout for better IDE support
2. **Unit Tests:** pytest coverage for all calculation functions
3. **Configuration Files:** YAML/TOML for parameters instead of hardcoded
4. **Logging Framework:** Replace print statements with proper logging
5. **Documentation:** Sphinx-generated API docs

## Troubleshooting

### Common Issues

**"No SL trades found"**
- Ensure `trades.csv` contains "SL" in `reward_risk` column
- Check data format consistency

**"No files passed distance filter"**
- R/R threshold may be too high
- Verify scoring formula matches your strategy expectations
- Check penalty calculation (trade_count / 20)

**Quality metric is None**
- max_losing_streak is 0 or negative
- All trades may be winners (rare edge case)
- Review losing streak calculation logic

**S3 upload fails**
- Verify credentials in `main.py`
- Check endpoint URL accessibility
- Confirm bucket exists and has write permissions

## License & Credits

This system was developed for backtesting analysis of trading strategies with emphasis on risk-adjusted performance metrics and multi-dimensional filtering.

**Key Design Principles:**
- Modular architecture for independent execution
- Consistent data flow and file naming
- Comprehensive logging for debugging
- Scalable to large datasets via NumPy vectorization
