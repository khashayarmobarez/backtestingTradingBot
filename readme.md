trading strategy:
the candle sizes and the time frame that i want the bot to work with is 4 hour time frames.

strategy on how to open the deals based on the candles:
1- each candle opens a deal.
2- the bot has infinite amount of money.
3- we open the deal on the end(close) of each candle and based on the price that the candle was closed.
4- the way that we decide if the deal is buy or seal is by seeing that the candle that was closed is bearish or bullish. if the deal was bearish we take a short(sell) position and if the candle was bullish we open a long(buy) position.
5- if the candle was bearish open the sell position 0.2(20 cents) lower than the closing point of the candle.
6- if the candle was bullish open the buy position 0.2(20 cents) higher than the opening point of the candle.
7- the way to set the stop loss of a short position(deal) is to see the highest amount that the candle reached(upper shadow). in a bearish candle the stop loss is the highest amount(point) the candle reached plus 0.2 dollar(20 cents). highest amount + 0.2(20 cents).
8- the way to set the stop loss of a long position is to see the lowest amount that the candle reached(lower shadow). in a bullish candle the stop loss of the position is the lowest amount(point) that candle reached(lower shodow) minus 0.2(20 cents). lowest amount - 0.2(20cents).
9- one important point is the position stays open until the stop loss is met.

the data that we need to record from the positions:
1- if the position is buy or sell
2- the distance value between the start of the position and the stop loss(call it distance value)
3- reward / risk. reward in the highest amount of profit that we could get in that position during the time that position was open. for example in sell position if the biggest amount that chart went down was 10$ in the position then came back up and hitted the stop loss, and the distance value was 2$. risk / reward would equal to 5. also if the reward/risk is lower than 1 return SL(stop loss intead of the number)
4- and the full date of when the position was opened.

cleaned prompt:

You are an expert trading bot developer.
I want you to rewrite and upgrade my backtesting trading bot based on the following complete trading strategy and data recording rules.
The bot must backtest on 4-hour candles, open positions based on candle behavior, and record all trade data in a CSV file for later analysis.

📈 Trading Strategy

Time Frame: 4-hour candles.

Entry Rules

The bot opens one new trade at the close of every candle.

The bot has infinite capital — ignore balance or position sizing.

Trade direction depends on the candle type:

Bullish candle (close > open): Open a Long (Buy) position.

Bearish candle (close < open): Open a Short (Sell) position.

Entry prices:

For a Long (Buy): enter at candle.close + 0.2 USD.

For a Short (Sell): enter at candle.close - 0.2 USD.

(The “0.2” is an absolute offset in USD, not a percentage.)

Stop-Loss Rules:

For Long (Buy) trades:
Stop loss = candle.low - 0.2 USD.

For Short (Sell) trades:
Stop loss = candle.high + 0.2 USD.

Each position stays open until its stop loss is triggered.
There is no take-profit — I just want to analyze data, not exit for profit.

Data Recording Rules:

For every trade, record the following:

Trade Type: "Buy" or "Sell".

Entry Price: the exact entry level.

Stop-Loss Price: the stop level for the position.

Distance Value: abs(entry - stop_loss) — the distance between entry and stop loss.

Max Profit:

For Buy: the highest price reached before the stop loss was hit, minus the entry.

For Sell: entry minus the lowest price reached before the stop loss was hit.

Reward/Risk Ratio: max_profit / distance_value.

Open Date: the exact date/time of the candle close when the trade was opened.

Output Requirements:

Save all results in a CSV file named trades.csv with columns:
date, type, entry, stop_loss, distance, max_profit, reward_risk.

At the end, print summary statistics:

Total trades

Average reward/risk

Average max profit

Development Requirements:

Fully rewrite the code for the backtesting bot using this logic.

Use clean, modular, and commented code so it’s easy to modify later.

Ensure data saving works properly (CSV format).

Goal:
Upgrade my backtesting bot to follow this exact candle-based trading logic, record complete trade data, and save everything in a CSV file for future analysis.
Use clean and well-structured code.
