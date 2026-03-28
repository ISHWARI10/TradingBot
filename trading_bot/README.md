# 📈 Binance Futures Testnet Trading Bot

A clean, production-quality Python CLI bot that places **MARKET** and **LIMIT** orders on
[Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # package marker
│   ├── client.py            # Binance client factory (testnet, .env keys)
│   ├── orders.py            # order placement logic & OrderResult dataclass
│   ├── validators.py        # input validation with descriptive error messages
│   ├── logging_config.py    # rotating file logger + quiet console handler
│   └── cli.py               # argparse CLI entry point
├── logs/
│   └── bot.log              # auto-created on first run
├── .env.example             # template – copy to .env and fill in keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | ≥ 3.10  |
| pip         | any     |

---

## Setup

### 1 — Clone / extract the project

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading_bot
```

### 2 — Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure API credentials

```bash
cp .env.example .env
```

Open `.env` in any text editor and paste your **Testnet** credentials:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> **How to get Testnet credentials**
> 1. Go to <https://testnet.binancefuture.com>
> 2. Log in with your GitHub account.
> 3. Click **API Management → Generate API Key**.
> 4. Copy the key and secret into your `.env` file.

⚠️ **Never commit `.env` to version control.** It is already in `.gitignore`.

---

## Running the Bot

The bot is invoked as a Python module from the project root:

```
python -m bot.cli [OPTIONS]
```

### Arguments

| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| `--symbol` | `-s` | ✅ | Trading pair, e.g. `BTCUSDT` |
| `--side` | `-d` | ✅ | `BUY` or `SELL` |
| `--type` | `-t` | ✅ | `MARKET` or `LIMIT` |
| `--quantity` | `-q` | ✅ | Positive number (base asset) |
| `--price` | `-p` | LIMIT only | Limit price |
| `--log-level` | — | ❌ | `DEBUG` / `INFO` / `WARNING` / `ERROR` (default: `DEBUG`) |

---

## Example Commands

### Market BUY — 0.001 BTC

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Console output:**

```
ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol             BTCUSDT
  Side               BUY
  Type               MARKET
  Quantity           0.001
  Price              (market price)
────────────────────────────────────────────────────────

⏳ Submitting order to Binance Futures Testnet …

ORDER RESPONSE
────────────────────────────────────────────────────────
  Order ID           3265489201
  Status             FILLED
  Symbol             BTCUSDT
  Side               BUY
  Type               MARKET
  Orig Qty           0.001
  Executed Qty       0.001
  Avg / Limit Price  57842.30
  Time In Force      GTC
  Client Order ID    x-HNA3LTNP7dfe3d9a2b14c
────────────────────────────────────────────────────────

✔  Order placed successfully!
   Log details saved to → logs/bot.log
```

---

### Limit SELL — 0.001 BTC at $100,000

```bash
python -m bot.cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000
```

**Console output:**

```
ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol             BTCUSDT
  Side               SELL
  Type               LIMIT
  Quantity           0.001
  Price              100000
────────────────────────────────────────────────────────

⏳ Submitting order to Binance Futures Testnet …

ORDER RESPONSE
────────────────────────────────────────────────────────
  Order ID           3265502847
  Status             NEW
  Symbol             BTCUSDT
  Side               SELL
  Type               LIMIT
  Orig Qty           0.001
  Executed Qty       0
  Avg / Limit Price  100000.00
  Time In Force      GTC
  Client Order ID    x-HNA3LTNP9af12cd874b1e
────────────────────────────────────────────────────────

✔  Order placed successfully!
   Log details saved to → logs/bot.log
```

---

### Short-form flags

```bash
# Market buy
python -m bot.cli -s BTCUSDT -d BUY -t MARKET -q 0.001

# Limit sell
python -m bot.cli -s BTCUSDT -d SELL -t LIMIT -q 0.001 -p 100000

# Another pair
python -m bot.cli -s DOGEUSDT -d BUY -t MARKET -q 100
```

---

### Help

```bash
python -m bot.cli --help
```

---

## Validation Examples

The bot gives clear, descriptive errors before hitting the API:

```bash
# Missing price on LIMIT order
$ python -m bot.cli -s BTCUSDT -d BUY -t LIMIT -q 0.001
✖  Validation error: Price is required for LIMIT orders. Provide it with --price <value>.

# Invalid side
$ python -m bot.cli -s BTCUSDT -d HOLD -t MARKET -q 0.001
✖  Validation error: Invalid side 'HOLD'. Allowed values: BUY, SELL.

# Negative quantity
$ python -m bot.cli -s BTCUSDT -d BUY -t MARKET -q -5
✖  Validation error: Quantity must be greater than zero. Got: -5.
```

---

## Logging

All logs are written to `logs/bot.log` using a **rotating file handler** (10 MB × 5 backups).
The console only shows `WARNING` and above, keeping terminal output clean.

Each log entry includes: timestamp · level · module · function · line · message.

```
2025-07-10 14:22:02 | INFO     | bot.client | get_client:69 | Binance Futures Testnet client ready. Ping OK.
2025-07-10 14:22:02 | INFO     | bot.orders | place_order:76 | Placing MARKET BUY order | symbol=BTCUSDT qty=0.001
2025-07-10 14:22:03 | INFO     | bot.orders | place_order:117 | Order placed successfully | orderId=3265489201 status=FILLED executedQty=0.001 avgPrice=57842.30
```

Sample log files (MARKET + LIMIT orders) are included in `logs/bot.log`.

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Missing / invalid CLI argument | Descriptive `ValidationError` printed; exits with code 1 |
| Missing `.env` keys | `ClientInitError` with setup instructions |
| Binance API rejection (bad symbol, filters) | API error code + message printed |
| Network timeout / DNS failure | Friendly network error message |
| Unexpected exception | Caught, printed, exits with code 1 |

All errors are also written to `logs/bot.log` at `ERROR` level.

---

## Assumptions

- Orders are placed on **Binance Futures Testnet (USDT-M)** only.
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default.
- Quantity precision must be compatible with Binance's lot-size filter for the chosen symbol
  (e.g. BTCUSDT minimum is typically `0.001`). The bot passes the value as-is; Binance will
  reject invalid precision with a descriptive API error.
- `colorama` is used for coloured output on all platforms; if not installed, output falls back
  to plain text gracefully.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-binance` | Binance REST API client with testnet support |
| `python-dotenv` | Load `.env` file into environment variables |
| `colorama` | Cross-platform ANSI colour codes |


