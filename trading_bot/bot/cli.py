"""
cli.py
------
Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:
  # Market buy
  python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit sell
  python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

  # Short form flags
  python -m bot.cli -s BTCUSDT -d BUY -t MARKET -q 0.001
"""

import argparse
import sys
import textwrap
from decimal import Decimal
from typing import Optional

from binance.exceptions import BinanceAPIException, BinanceRequestException

from .client import ClientInitError
from .logging_config import setup_logging
from .orders import place_order
from .validators import ValidationError, validate_all

# ── ANSI colour helpers (disabled automatically on Windows without ANSI support)
try:
    import colorama
    colorama.init(autoreset=True)
    GREEN  = colorama.Fore.GREEN
    RED    = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    CYAN   = colorama.Fore.CYAN
    BOLD   = colorama.Style.BRIGHT
    RESET  = colorama.Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


# ─────────────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description=textwrap.dedent(
            """\
            Binance Futures Testnet (USDT-M) – Trading Bot
            ─────────────────────────────────────────────────
            Place MARKET or LIMIT orders directly from the command line.
            API keys are read from the .env file in the project root.
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              Market buy  0.001 BTC:
                python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

              Limit sell  0.001 BTC at $100,000:
                python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

              Market buy  10 DOGE:
                python -m bot.cli -s DOGEUSDT -d BUY -t MARKET -q 10
            """
        ),
    )

    parser.add_argument(
        "-s", "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT, ETHUSDT, DOGEUSDT.",
    )
    parser.add_argument(
        "-d", "--side",
        required=True,
        metavar="SIDE",
        help="Order direction: BUY or SELL.",
    )
    parser.add_argument(
        "-t", "--type",
        required=True,
        metavar="ORDER_TYPE",
        dest="order_type",
        help="Order type: MARKET or LIMIT.",
    )
    parser.add_argument(
        "-q", "--quantity",
        required=True,
        metavar="QTY",
        help="Order quantity (base asset). Must be a positive number.",
    )
    parser.add_argument(
        "-p", "--price",
        required=False,
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT orders, ignored for MARKET).",
    )
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Minimum log level written to bot.log (default: DEBUG).",
    )

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-printing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _divider(char: str = "─", width: int = 56) -> str:
    return char * width


def print_request_summary(symbol: str, side: str, order_type: str,
                           quantity: Decimal, price: Optional[Decimal]) -> None:
    """Print a clean summary of the order that is about to be placed."""
    print()
    print(f"{BOLD}{CYAN}{'ORDER REQUEST SUMMARY':^56}{RESET}")
    print(_divider())
    print(f"  {'Symbol':<18} {BOLD}{symbol}{RESET}")
    print(f"  {'Side':<18} {BOLD}{side}{RESET}")
    print(f"  {'Type':<18} {BOLD}{order_type}{RESET}")
    print(f"  {'Quantity':<18} {BOLD}{quantity}{RESET}")
    if price is not None:
        print(f"  {'Price':<18} {BOLD}{price}{RESET}")
    else:
        print(f"  {'Price':<18} {BOLD}(market price){RESET}")
    print(_divider())
    print()


def print_order_response(result) -> None:
    """Print the key fields from the Binance order response."""
    print(f"{BOLD}{CYAN}{'ORDER RESPONSE':^56}{RESET}")
    print(_divider())
    print(f"  {'Order ID':<18} {result.order_id}")
    print(f"  {'Status':<18} {result.status}")
    print(f"  {'Symbol':<18} {result.symbol}")
    print(f"  {'Side':<18} {result.side}")
    print(f"  {'Type':<18} {result.order_type}")
    print(f"  {'Orig Qty':<18} {result.orig_qty}")
    print(f"  {'Executed Qty':<18} {result.executed_qty}")
    if result.avg_price:
        print(f"  {'Avg / Limit Price':<18} {result.avg_price}")
    if result.time_in_force:
        print(f"  {'Time In Force':<18} {result.time_in_force}")
    print(f"  {'Client Order ID':<18} {result.client_order_id}")
    print(_divider())
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    """
    Parse arguments, validate inputs, place the order, and print results.

    Returns:
        0 on success, 1 on any error (suitable for sys.exit).
    """
    parser = build_parser()
    args   = parser.parse_args(argv)

    # Initialise logging as early as possible
    setup_logging(log_level=args.log_level)

    # ── 1. Validate all inputs ────────────────────────────────────────────────
    try:
        validated = validate_all(
            symbol     = args.symbol,
            side       = args.side,
            order_type = args.order_type,
            quantity   = args.quantity,
            price      = args.price,
        )
    except ValidationError as exc:
        print(f"\n{RED}✖  Validation error:{RESET} {exc}\n", file=sys.stderr)
        return 1

    symbol     = validated["symbol"]
    side       = validated["side"]
    order_type = validated["order_type"]
    quantity   = validated["quantity"]
    price      = validated["price"]

    # ── 2. Print what we're about to do ──────────────────────────────────────
    print_request_summary(symbol, side, order_type, quantity, price)
    print(f"{YELLOW}⏳ Submitting order to Binance Futures Testnet …{RESET}\n")

    # ── 3. Place the order ────────────────────────────────────────────────────
    try:
        result = place_order(
            symbol     = symbol,
            side       = side,
            order_type = order_type,
            quantity   = quantity,
            price      = price,
        )
    except ClientInitError as exc:
        print(f"\n{RED}✖  Client initialisation failed:{RESET}\n  {exc}\n", file=sys.stderr)
        return 1
    except BinanceAPIException as exc:
        print(
            f"\n{RED}✖  Binance API error (code {exc.code}):{RESET}\n  {exc.message}\n",
            file=sys.stderr,
        )
        return 1
    except BinanceRequestException as exc:
        print(
            f"\n{RED}✖  Network error:{RESET}\n  {exc}\n"
            "  Check your internet connection and try again.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001 – catch-all safety net
        print(f"\n{RED}✖  Unexpected error:{RESET} {exc}\n", file=sys.stderr)
        return 1

    # ── 4. Print the result ───────────────────────────────────────────────────
    print_order_response(result)
    print(f"{GREEN}✔  Order placed successfully!{RESET}")
    print(f"   Log details saved to → logs/bot.log\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
