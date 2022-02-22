# Cryptobot

There are various stablecoins with prices pegged to $1, as well as certain tokens pegged to the price of other tokens. This leaves arbitrage opportunities between pairs of tokens when there is volatility in the crypto market.
This swap_bot will set and complete a limit order swap based on the ratios specified between token pairs. 

A connection to the network you want to trade on and a local account through the brownie module will be prerequisites. An API key will also be necessary for the various network. There also needs to be a balance in one of the token pairs, as well as a balance for network token in local account or gas fees.

Phone number, email address, and email app secure password are needed variables for text alerts after confirmed swap. Can comment out email_alert if not wanted.

Router, liquidity pool, and token addresses need to be verified on the network scanner. This is currently an outline for the TOMB-WFTM token pair on Fantom. Router needs to be Uniswapv2 or fork.

DRY_RUN set to TRUE will still monitor potential trades but will not perform swaps, so no token balances are needed.

ONE_SHOT set to TRUE will stop after one trade, if set to FALSE, then it will continue trading tokens back and forth if both pair ratios are specified in the set_swap_target in swap_bot.
 
Next: Create config file for all variables. Edit code where variables are no longer needed to be changed manually.

