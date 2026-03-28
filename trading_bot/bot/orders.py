"""
orders.py
---------
Order-placement logic for Binance Futures (USDT-M) Testnet.

This module owns the API call layer.  The CLI layer (cli.py) is responsible only
for parsing inputs, validating them, and printing results – it never touches the
Binance client directly.
"""

import logging
from decimal import Decimal
from typing import Optional

from binance.exceptions import BinanceAPIException, BinanceRequestException

from .client import get_client

log = logging.getLogger(__name__)


# ── Public data structure ──────────────────────────────────────────────────────

class OrderResult:
    """Structured representation of a placed order."""

    def __init__(self, raw: dict):
        self.raw          = raw
        self.order_id     = raw.get("orderId")
        self.symbol       = raw.get("symbol")
        self.status       = raw.get("status")
        self.side         = raw.get("side")
        self.order_type   = raw.get("type")
        self.orig_qty     = raw.get("origQty")
        self.executed_qty = raw.get("executedQty")
        self.avg_price    = raw.get("avgPrice") or raw.get("price")
        self.time_in_force= raw.get("timeInForce")
        self.client_order_id = raw.get("clientOrderId")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OrderResult(orderId={self.order_id}, symbol={self.symbol}, "
            f"status={self.status}, executedQty={self.executed_qty})"
        )


# ── Internal helpers ───────────────────────────────────────────────────────────

def _format_decimal(value: Decimal) -> str:
    """
    Format a Decimal for the Binance API: remove trailing zeros, no scientific notation.
    E.g. Decimal('0.001000') → '0.001'
    """
    return f"{value.normalize():f}"


# ── Public API ─────────────────────────────────────────────────────────────────

def place_order(
    symbol:     str,
    side:       str,
    order_type: str,
    quantity:   Decimal,
    price:      Optional[Decimal] = None,
) -> OrderResult:
    """
    Place a MARKET or LIMIT order on Binance Futures Testnet (USDT-M).

    Args:
        symbol:     Trading pair, e.g. 'BTCUSDT'.
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Order quantity (base asset).
        price:      Limit price (required for LIMIT, ignored for MARKET).

    Returns:
        OrderResult wrapping the raw Binance API response.

    Raises:
        BinanceAPIException:     API returned an error (bad symbol, insufficient
                                 balance, price filter violation, etc.).
        BinanceRequestException: Network-level failure (timeout, DNS, etc.).
        ValueError:              Unexpected order_type passed (defensive guard).
    """
    client = get_client()
    qty_str = _format_decimal(quantity)

    # ── Build kwargs shared by all order types ────────────────────────────────
    params: dict = {
        "symbol":   symbol,
        "side":     side,
        "type":     order_type,
        "quantity": qty_str,
    }

    if order_type == "MARKET":
        log.info(
            "Placing MARKET %s order | symbol=%s qty=%s",
            side, symbol, qty_str,
        )

    elif order_type == "LIMIT":
        if price is None:
            raise ValueError("price must be provided for LIMIT orders.")
        price_str = _format_decimal(price)
        params["price"]       = price_str
        params["timeInForce"] = "GTC"   # Good Till Cancelled is the standard default
        log.info(
            "Placing LIMIT %s order  | symbol=%s qty=%s price=%s timeInForce=GTC",
            side, symbol, qty_str, price_str,
        )

    else:
        raise ValueError(f"Unsupported order type: {order_type!r}")

    log.debug("API request payload: %s", params)

    try:
        response = client.futures_create_order(**params)
    except BinanceAPIException as exc:
        log.error(
            "Binance API error placing %s %s %s order: code=%s msg=%s",
            order_type, side, symbol, exc.code, exc.message,
        )
        raise
    except BinanceRequestException as exc:
        log.error(
            "Network error placing %s %s %s order: %s",
            order_type, side, symbol, exc,
        )
        raise

    log.debug("API raw response: %s", response)
    result = OrderResult(response)
    log.info(
        "Order placed successfully | orderId=%s status=%s executedQty=%s avgPrice=%s",
        result.order_id, result.status, result.executed_qty, result.avg_price,
    )
    return result
