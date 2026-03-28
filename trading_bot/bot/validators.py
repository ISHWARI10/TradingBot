"""
validators.py
-------------
All input-validation logic lives here so that both the CLI layer and any future
API/web layer can reuse the same rules without duplication.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

log = logging.getLogger(__name__)

# ── Allowed values ─────────────────────────────────────────────────────────────
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    """
    Ensure the trading symbol is a non-empty uppercase alphanumeric string.

    Args:
        symbol: Raw symbol string from the user (e.g. 'btcusdt').

    Returns:
        Uppercased, stripped symbol (e.g. 'BTCUSDT').

    Raises:
        ValidationError: If the symbol is empty or contains invalid characters.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol must not be empty.")
    if not symbol.isalnum():
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Use only letters and digits (e.g. BTCUSDT)."
        )
    log.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    """
    Ensure the order side is BUY or SELL.

    Args:
        side: Raw side string from the user.

    Returns:
        Uppercased side ('BUY' or 'SELL').

    Raises:
        ValidationError: If the side is not recognised.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Allowed values: {', '.join(sorted(VALID_SIDES))}."
        )
    log.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    """
    Ensure the order type is MARKET or LIMIT.

    Args:
        order_type: Raw order-type string from the user.

    Returns:
        Uppercased order type ('MARKET' or 'LIMIT').

    Raises:
        ValidationError: If the order type is not recognised.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Allowed values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    log.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """
    Ensure the quantity is a positive number.

    Args:
        quantity: Raw quantity value (string or float) from the user.

    Returns:
        Validated quantity as a Decimal for precision arithmetic.

    Raises:
        ValidationError: If the quantity is not a valid positive number.
    """
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValidationError(
            f"Quantity '{quantity}' is not a valid number."
        )
    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than zero. Got: {qty}."
        )
    log.debug("Quantity validated: %s", qty)
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate the price field according to the order type.

    - LIMIT orders: price is *required* and must be a positive number.
    - MARKET orders: price is *ignored* (returns None).

    Args:
        price:      Raw price value from the user (may be None).
        order_type: Already-validated order type string.

    Returns:
        Validated price as Decimal, or None for MARKET orders.

    Raises:
        ValidationError: If price is missing for a LIMIT order or is non-positive.
    """
    if order_type == "MARKET":
        if price is not None:
            log.debug("Price argument ignored for MARKET order.")
        return None

    # LIMIT — price is required
    if price is None:
        raise ValidationError(
            "Price is required for LIMIT orders. "
            "Provide it with --price <value>."
        )
    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError(
            f"Price '{price}' is not a valid number."
        )
    if p <= 0:
        raise ValidationError(
            f"Price must be greater than zero. Got: {p}."
        )
    log.debug("Price validated: %s", p)
    return p


def validate_all(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
) -> dict:
    """
    Convenience function: validate all inputs in one call.

    Returns:
        A dict with keys: symbol, side, order_type, quantity, price.

    Raises:
        ValidationError: On the first validation failure encountered.
    """
    symbol     = validate_symbol(symbol)
    side       = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity   = validate_quantity(quantity)
    price      = validate_price(price, order_type)

    return {
        "symbol":     symbol,
        "side":       side,
        "order_type": order_type,
        "quantity":   quantity,
        "price":      price,
    }
