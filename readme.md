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
1-
