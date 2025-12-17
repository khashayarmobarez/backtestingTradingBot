import pandas as pd
import numpy as np
from datetime import datetime

# ===============================================================
#  CONFIGURATION
# ===============================================================

CONFIG = {
    "INITIAL_CAPITAL": 5000,
    "POSITION_SIZE_PERCENT": 0.029,  # 2.9% of available capital
    "ENTRY_OFFSET": 0.2,  # USD offset for entry
    "SL_OFFSET": 0.2,  # USD offset for stop loss
    "DATA_FILE": "gold_data.csv",
    "OUTPUT_FILE": "trades2.csv",
    "EXCLUDED_TIME": "01:30",  # 1:30am excluded time
}

# Distance filters (rounded down)
DISTANCE_FILTERS = {
    "buy": [
        3,
        (6, 10),  # 6 till 10 (inclusive)
        12,
        14,
        (16, 17),
        19,
        23,
        26,
        28,
        31,
        (36, 37),
        (42, 45),
        (47, 48),
        (52, 56),
        (58, 71),
        59,
    ],
    "sell": [
        2,
        (4, 11),
        (13, 19),
        (21, 22),
        (24, 25),
        29,
        (31, 34),
        (36, 38),
        40,
        42,
        47,
        (49, 56),
        58,
        (62, 64),
        (67, 72),
        74,
        (77, 94),
    ],
}


# ===============================================================
#  HELPER FUNCTIONS
# ===============================================================

def is_distance_filtered(distance, trade_type):
    """
    Check if a distance value is in the filter list
    """
    rounded_distance = int(np.floor(distance))
    filters = DISTANCE_FILTERS[trade_type.lower()]

    for f in filters:
        if isinstance(f, tuple):
            # Range check
            min_val, max_val = f
            if min_val <= rounded_distance <= max_val:
                return True
        else:
            # Single value check
            if rounded_distance == f:
                return True

    return False


def get_trade_type(candle):
    """
    Determine trade type based on candle
    """
    return "Buy" if candle["close"] > candle["open"] else "Sell"


def calculate_entry(candle, trade_type):
    """
    Calculate entry price
    """
    if trade_type == "Buy":
        return candle["close"] + CONFIG["ENTRY_OFFSET"]
    else:
        return candle["close"] - CONFIG["ENTRY_OFFSET"]


def calculate_stop_loss(candle, trade_type):
    """
    Calculate stop loss
    """
    if trade_type == "Buy":
        return candle["low"] - CONFIG["SL_OFFSET"]
    else:
        return candle["high"] + CONFIG["SL_OFFSET"]


def calculate_distance(entry, stop_loss):
    """
    Calculate distance
    """
    return abs(entry - stop_loss)


def calculate_take_profit(entry, distance, trade_type):
    """
    Calculate take profit (1:1 R/R)
    """
    if trade_type == "Buy":
        return entry + distance
    else:
        return entry - distance


def check_trade_status(trade, candle):
    """
    Check if a trade hits SL or TP on a given candle
    """
    if trade["status"] != "open":
        return

    if trade["type"] == "Buy":
        # Check stop loss
        if candle["low"] <= trade["stop_loss"]:
            trade["status"] = "closed"
            trade["exit_price"] = trade["stop_loss"]
            trade["exit_date"] = f"{candle['date']} {candle['time']}"
            trade["profit"] = -trade["distance"] * trade["position_size"]
            trade["reward_risk"] = 0  # Hit SL = 0 R/R
            return
        # Check take profit
        if candle["high"] >= trade["take_profit"]:
            trade["status"] = "closed"
            trade["exit_price"] = trade["take_profit"]
            trade["exit_date"] = f"{candle['date']} {candle['time']}"
            trade["profit"] = trade["distance"] * trade["position_size"]
            trade["reward_risk"] = 1  # Hit TP = 1:1 R/R
            return
    else:
        # Sell trade
        # Check stop loss
        if candle["high"] >= trade["stop_loss"]:
            trade["status"] = "closed"
            trade["exit_price"] = trade["stop_loss"]
            trade["exit_date"] = f"{candle['date']} {candle['time']}"
            trade["profit"] = -trade["distance"] * trade["position_size"]
            trade["reward_risk"] = 0
            return
        # Check take profit
        if candle["low"] <= trade["take_profit"]:
            trade["status"] = "closed"
            trade["exit_price"] = trade["take_profit"]
            trade["exit_date"] = f"{candle['date']} {candle['time']}"
            trade["profit"] = trade["distance"] * trade["position_size"]
            trade["reward_risk"] = 1
            return


def calculate_unrealized_pnl(trade, current_price):
    """
    Calculate unrealized P&L for open positions
    """
    if trade["status"] != "open":
        return 0

    if trade["type"] == "Buy":
        return (current_price - trade["entry"]) * trade["position_size"]
    else:
        return (trade["entry"] - current_price) * trade["position_size"]


def get_day_of_week(date_str):
    """
    Get day of week from date string (YYYY.MM.DD)
    """
    year, month, day = map(int, date_str.split('.'))
    date_obj = datetime(year, month, day)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[date_obj.weekday()]


# ===============================================================
#  MAIN BACKTESTING ENGINE
# ===============================================================

def run_backtest():
    print("=" * 70)
    print("  GOLD TRADING BACKTEST BOT")
    print("=" * 70)
    print()

    # Load data
    print(f"📊 Loading data from {CONFIG['DATA_FILE']}...")
    candles_df = pd.read_csv(
        CONFIG["DATA_FILE"],
        names=["date", "time", "open", "high", "low", "close", "volume"]
    )
    
    print(f"✅ Loaded {len(candles_df)} candles")
    print(f"📅 Date range: {candles_df.iloc[0]['date']} to {candles_df.iloc[-1]['date']}")
    print()

    # Initialize
    capital = CONFIG["INITIAL_CAPITAL"]
    all_trades = []
    open_positions = []
    yearly_capital = {}

    total_trades_opened = 0
    total_trades_filtered = 0

    # Process each candle
    for idx, candle in candles_df.iterrows():
        # Update all open positions
        for trade in open_positions:
            check_trade_status(trade, candle)
            
            # If closed, update capital
            if trade["status"] == "closed":
                capital += trade["profit"]

        # Remove closed positions
        open_positions = [t for t in open_positions if t["status"] == "open"]

        # Check if we should skip this candle for opening new trades
        if candle["time"] == CONFIG["EXCLUDED_TIME"]:
            continue

        # Determine trade parameters
        trade_type = get_trade_type(candle)
        entry = calculate_entry(candle, trade_type)
        stop_loss = calculate_stop_loss(candle, trade_type)
        distance = calculate_distance(entry, stop_loss)

        # Check distance filter
        if is_distance_filtered(distance, trade_type):
            total_trades_filtered += 1
            continue

        # -------------------------------------------------------------
        #  CALCULATE AVAILABLE MONEY & POSITION SIZE
        # -------------------------------------------------------------
        
        # Calculate how much money is currently tied up in open trades
        current_used_capital = sum(t["entry"] * t["position_size"] for t in open_positions)
        
        # Determine available money (Free Margin)
        available_capital = capital - current_used_capital
        
        # If we have no money left or negative, we cannot open a trade
        if available_capital <= 0:
            continue

        # Calculate position size based on 2.9% of AVAILABLE capital
        position_size = (available_capital * CONFIG["POSITION_SIZE_PERCENT"]) / entry
        
        # Calculate exactly how much money is being used for this trade
        money_used = position_size * entry

        # -------------------------------------------------------------
        #  END CALCULATION SECTION
        # -------------------------------------------------------------
        
        take_profit = calculate_take_profit(entry, distance, trade_type)

        # Create new trade
        trade = {
            "id": total_trades_opened + 1,
            "type": trade_type,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "distance": distance,
            "position_size": position_size,
            "money_used": money_used,
            "open_date": f"{candle['date']} {candle['time']}",
            "status": "open",
            "profit": 0,
            "reward_risk": None,
            "exit_price": None,
            "exit_date": None,
        }

        open_positions.append(trade)
        all_trades.append(trade)
        total_trades_opened += 1

        # Track yearly capital
        year = candle["date"].split('.')[0]
        yearly_capital[year] = capital

    # Calculate final capital including unrealized P&L
    last_candle = candles_df.iloc[-1]
    unrealized_pnl = sum(calculate_unrealized_pnl(t, last_candle["close"]) for t in open_positions)
    final_capital = capital + unrealized_pnl

    # Mark remaining open positions with "SL" for reward_risk
    for trade in all_trades:
        if trade["status"] == "open":
            trade["reward_risk"] = "SL"  # Still open at end = treat as SL for CSV
            trade["exit_price"] = last_candle["close"]
            trade["exit_date"] = f"{last_candle['date']} {last_candle['time']}"
            trade["profit"] = calculate_unrealized_pnl(trade, last_candle["close"])

    # ===============================================================
    #  SAVE RESULTS TO CSV
    # ===============================================================

    print("\n📝 Saving results to CSV...")
    
    csv_data = []
    for trade in all_trades:
        date, time = trade["open_date"].split(' ')
        day_of_week = get_day_of_week(date)
        max_profit = trade["profit"]
        reward_risk = "SL" if trade["reward_risk"] is None else trade["reward_risk"]
        
        csv_data.append({
            "date": date,
            "time": time,
            "day_of_week": day_of_week,
            "type": trade["type"],
            "entry": round(trade["entry"], 2),
            "stop_loss": round(trade["stop_loss"], 2),
            "distance": round(trade["distance"], 2),
            # "trade_size" REMOVED as requested
            "money_used": round(trade["money_used"], 2),
            "max_profit": round(max_profit, 2),
            "reward_risk": reward_risk
        })


    trades_df = pd.DataFrame(csv_data)
    trades_df.to_csv(CONFIG["OUTPUT_FILE"], index=False)
    print(f"✅ Saved {len(all_trades)} trades to {CONFIG['OUTPUT_FILE']}")

    # ===============================================================
    #  PRINT SUMMARY STATISTICS
    # ===============================================================

    print("\n" + "=" * 70)
    print("  BACKTEST SUMMARY")
    print("=" * 70)
    print()

    print(f"💰 Initial Capital: ${CONFIG['INITIAL_CAPITAL']:.2f}")
    print(f"💰 Final Capital (with unrealized P&L): ${final_capital:.2f}")
    print(f"📈 Total Return: {((final_capital / CONFIG['INITIAL_CAPITAL'] - 1) * 100):.2f}%")
    print(f"📊 Total Profit/Loss: ${(final_capital - CONFIG['INITIAL_CAPITAL']):.2f}")
    print()

    print(f"📋 Total Trades Opened: {total_trades_opened}")
    print(f"🚫 Total Trades Filtered: {total_trades_filtered}")
    print(f"📂 Open Positions: {len(open_positions)}")
    print()

    # Calculate win rate
    closed_trades = [t for t in all_trades if t["reward_risk"] != "SL" and t["reward_risk"] is not None]
    winning_trades = [t for t in closed_trades if t["reward_risk"] > 0]
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
    
    print(f"🎯 Win Rate: {win_rate:.2f}% ({len(winning_trades)}/{len(closed_trades)})")
    
    # Calculate average R/R
    avg_rr = (sum(t["reward_risk"] for t in closed_trades) / len(closed_trades)) if closed_trades else 0
    print(f"📊 Average Reward/Risk: {avg_rr:.2f}")
    print()

    # Yearly capital
    print("📅 Capital by Year:")
    for year in sorted(yearly_capital.keys()):
        year_capital = yearly_capital[year]
        year_return = ((year_capital / CONFIG["INITIAL_CAPITAL"] - 1) * 100)
        print(f"   {year}: ${year_capital:.2f} ({year_return:.2f}% return)")

    print()
    print("=" * 70)
    print("  BACKTEST COMPLETE!")
    print("=" * 70)


# ===============================================================
#  MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    try:
        run_backtest()
    except FileNotFoundError:
        print(f"❌ Error: {CONFIG['DATA_FILE']} not found!")
        print("Please make sure the gold_data.csv file is in the same directory.")
    except Exception as e:
        print(f"❌ Error running backtest: {str(e)}")
        import traceback
        traceback.print_exc()