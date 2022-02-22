import sys, time, os
import brownie
from Class.token import Erc20Token
from Class.router import Router
from Class.liquiditypool import LiquidityPool
from Class.text_msgs import email_alert
from decimal import Decimal
from dotenv import load_dotenv


load_dotenv()

BROWNIE_USERNAME = os.getenv("BROWNIE_USERNAME")
BROWNIE_PASSWORD = os.getenv("BROWNIE_PASSWORD")
BROWNIE_ACCOUNT = (BROWNIE_USERNAME, BROWNIE_PASSWORD)
BROWNIE_FTM_NETWORK = os.getenv("BROWNIE_FTM_NETWORK")
FTMSCAN_API_KEY = os.getenv("FTMSCAN_API_KEY")
os.environ["FTMSCAN_TOKEN"] = FTMSCAN_API_KEY

EMAIL = os.getenv("EMAIL")
EMAIL_PWORD = os.getenv("EMAIL_PWORD")
PHONE_NUM = os.getenv("PHONE_NUM")

# Contract addresses (verify on Scanner)
SPOOKYSWAP_ROUTER_CONTRACT_ADDRESS = "0xF491e7B69E4244ad4002BC14e878a34207E38c29"
SPOOKYSWAP_POOL_CONTRACT_ADDRESS = "0x2a651563c9d3af67ae0388a5c8f89b867038089e"
WFTM_CONTRACT_ADDRESS = "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83"
TOMB_CONTRACT_ADDRESS = "0x6c021Ae822BEa943b2E66552bDe1D2696a53fbB7"

SLIPPAGE = Decimal("0.001")  # optional tolerated slippage in swap price (0.1%)

# Simulate swaps and approvals
DRY_RUN = False
# Quit after the first successful trade
ONE_SHOT = False
# How often to run the main loop (in seconds)
LOOP_TIME = 0.5


def main():

    try:
        brownie.network.connect(BROWNIE_FTM_NETWORK)
    except:
        sys.exit(
            "Could not connect! Verify your Brownie network settings using 'brownie networks list'"
        )

    try:
        cryptobot = brownie.accounts.load(BROWNIE_USERNAME, password=BROWNIE_PASSWORD)
    except:
        sys.exit(
            "Could not load account! Verify your Brownie account settings using 'brownie accounts list'"
        )

    tomb = Erc20Token(
        address=TOMB_CONTRACT_ADDRESS,
        user=cryptobot,
        # abi=ERC20
    )

    wftm = Erc20Token(
        address=WFTM_CONTRACT_ADDRESS,
        user=cryptobot,
        # abi=ERC20
    )

    tokens = [
        tomb,
        wftm,
    ]

    spookyswap_router = Router(
        address=SPOOKYSWAP_ROUTER_CONTRACT_ADDRESS,
        name="SpookySwap Router",
        user=cryptobot,
        # abi=UNISWAPV2_ROUTER,
    )

    spookyswap_lp = LiquidityPool(
        address=SPOOKYSWAP_POOL_CONTRACT_ADDRESS,
        name="SpookySwap: TOMB-WFTM",
        router=spookyswap_router,
        # abi=UNISWAPV2_LP,
        tokens=tokens,
        update_method="polling",
        fee=Decimal("0.003"),
    )

    lps = [
        spookyswap_lp,
    ]

    routers = [
        spookyswap_router,
    ]

    # Confirm approvals for all tokens on every router
    print()
    print("Approvals:")
    for router in routers:
        for token in tokens:
            if not token.get_approval(external_address=router.address) and not DRY_RUN:
                token.set_approval(external_address=router.address, value=-1)
            else:
                print(f"{token} on {router} OK")

    print()
    print("Swap Targets:")
    for lp in lps:
        lp.set_swap_target(
            token_in_qty=1,
            token_in=tomb,
            token_out_qty=1.01,
            token_out=wftm,
        )

        lp.set_swap_target(
            token_in_qty=1,
            token_in=wftm,
            token_out_qty=1.01,
            token_out=tomb,
        )

    balance_refresh = True

    #
    # Start of main loop
    #

    while True:

        try:
            if brownie.network.is_connected():
                pass
            else:
                print("Network connection lost! Reconnecting...")
                if brownie.network.connect(BROWNIE_FTM_NETWORK):
                    pass
                else:
                    time.sleep(5)
                    continue
        except:
            # restart loop
            continue

        loop_start = time.time()

        if balance_refresh:
            print()
            print("Account Balance:")
            for token in tokens:
                token.update_balance()
                print(f"• {token.normalized_balance} {token.symbol} ({token.name})")
                balance_refresh = False

        for lp in lps:
            lp.update_reserves(print_reserves=False)

            if lp.token0.balance and lp.token0_max_swap:
                token_in = lp.token0
                token_out = lp.token1
                # finds maximum token1 input at desired ratio
                token_in_qty = min(lp.token0.balance, lp.token0_max_swap)
                # calculate output from maximum input above
                token_out_qty = lp.calculate_tokens_out_from_tokens_in(
                    token_in=lp.token0,
                    token_in_quantity=token_in_qty,
                )
                print(
                    f"*** EXECUTING SWAP ON {str(lp.router).upper()} OF {token_in_qty / (10 ** token_in.decimals)} {token_in} FOR {token_out_qty / (10 ** token_out.decimals)} {token_out} ***"
                )
                if not DRY_RUN:
                    lp.router.token_swap(
                        token_in_quantity=token_in_qty,
                        token_in_address=token_in.address,
                        token_out_quantity=token_out_qty,
                        token_out_address=token_out.address,
                        slippage=SLIPPAGE,
                    )
                    balance_refresh = True
                    email_alert(
                        EMAIL, EMAIL_PWORD, "Swap Alert", "Trade confirmed", PHONE_NUM
                    )
                    if ONE_SHOT:
                        sys.exit("single shot complete!")
                    break

            if lp.token1.balance and lp.token1_max_swap:
                token_in = lp.token1
                token_out = lp.token0
                # finds maximum token1 input at desired ratio
                token_in_qty = min(lp.token1.balance, lp.token1_max_swap)
                # calculate output from maximum input above
                token_out_qty = lp.calculate_tokens_out_from_tokens_in(
                    token_in=lp.token1,
                    token_in_quantity=token_in_qty,
                )
                print(
                    f"*** EXECUTING SWAP ON {str(lp.router).upper()} OF {token_in_qty / (10 ** token_in.decimals)} {token_in} FOR {token_out_qty / (10 ** token_out.decimals)} {token_out} ***"
                )
                if not DRY_RUN:
                    lp.router.token_swap(
                        token_in_quantity=token_in_qty,
                        token_in_address=token_in.address,
                        token_out_quantity=token_out_qty,
                        token_out_address=token_out.address,
                        slippage=SLIPPAGE,
                    )
                    balance_refresh = True
                    email_alert(
                        EMAIL, EMAIL_PWORD, "Swap Alert", "Trade confirmed", PHONE_NUM
                    )
                    if ONE_SHOT:
                        sys.exit("single shot complete!")
                    break

        loop_end = time.time()

        # Control the loop timing more precisely by measuring start and end time and sleeping as needed
        if (loop_end - loop_start) >= LOOP_TIME:
            continue
        else:
            time.sleep(LOOP_TIME - (loop_end - loop_start))
            continue

    #
    # End of main loop
    #


# Only executes main loop if this file is called directly
if __name__ == "__main__":
    main()
