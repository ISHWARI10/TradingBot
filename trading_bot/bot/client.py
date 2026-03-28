"""
client.py
---------
Thin wrapper around python-binance that:
  - loads API keys from a .env file
  - points at the Binance Futures USDT-M Testnet
  - exposes a single get_client() factory used by the rest of the bot
"""

import logging
import os
from functools import lru_cache

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

log = logging.getLogger(__name__)

# ── Testnet base URLs ──────────────────────────────────────────────────────────
FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"

# python-binance uses separate URL constants for futures testnet
FUTURES_TESTNET_URL = "https://testnet.binancefuture.com/fapi"
FUTURES_TESTNET_WS  = "wss://stream.binancefuture.com/ws"


class ClientInitError(RuntimeError):
    """Raised when the Binance client cannot be initialised."""


@lru_cache(maxsize=1)
def get_client() -> Client:
    """
    Build and return a cached Binance client configured for the Futures Testnet.

    API keys are read from the environment (populated by python-dotenv from .env).

    Returns:
        Authenticated binance.Client instance.

    Raises:
        ClientInitError: If keys are missing or the initial ping fails.
    """
    load_dotenv()  # no-op if already loaded; safe to call multiple times

    api_key    = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        raise ClientInitError(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file.\n"
            "  1. Copy .env.example → .env\n"
            "  2. Paste your Testnet credentials from https://testnet.binancefuture.com"
        )

    log.debug("Initialising Binance Futures Testnet client …")

    try:
        client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True,           # switches python-binance to testnet endpoints
        )

        # Override the futures base URL explicitly to be safe
        client.FUTURES_URL = FUTURES_TESTNET_URL

        # Quick connectivity check – raises on network/auth issues
        client.futures_ping()
        log.info("Binance Futures Testnet client ready. Ping OK.")

    except BinanceAPIException as exc:
        log.error("Binance API error during client init: %s", exc)
        raise ClientInitError(
            f"Binance API rejected the credentials (code {exc.code}): {exc.message}"
        ) from exc
    except BinanceRequestException as exc:
        log.error("Network error during client init: %s", exc)
        raise ClientInitError(
            f"Could not reach Binance Testnet ({FUTURES_TESTNET_BASE_URL}). "
            "Check your internet connection."
        ) from exc

    return client
