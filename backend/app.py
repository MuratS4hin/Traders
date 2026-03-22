"""
Flask API for the Traders backend.

Endpoints
---------
GET  /stocks               – Pivot point data for all top-20 stocks
GET  /stocks/<ticker>      – Pivot point data for a single stock
POST /trade                – Execute a demo trade for a given ticker
GET  /transactions         – View all logged transactions
GET  /transactions/<ticker>– View transactions for a specific ticker
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

from stocks import TOP_20_TICKERS, get_latest_ohlc
from pivot import calculate_pivot_points, trading_signal
from transactions import init_db, record_transaction, get_all_transactions, get_transactions_by_ticker

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_stock_payload(ticker: str) -> dict:
    """Fetch OHLC, compute pivot points and signal for a ticker."""
    ohlc = get_latest_ohlc(ticker)
    levels = calculate_pivot_points(ohlc["high"], ohlc["low"], ohlc["close"])
    signal = trading_signal(ohlc["close"], levels)
    return {
        "ticker": ticker,
        "ohlc": ohlc,
        "pivot_points": levels,
        "signal": signal,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/stocks", methods=["GET"])
def get_all_stocks():
    """Return pivot point data for all top-20 stocks."""
    results = []
    errors = []
    for ticker in TOP_20_TICKERS:
        try:
            results.append(_build_stock_payload(ticker))
        except Exception as exc:
            errors.append({"ticker": ticker, "error": str(exc)})

    return jsonify({"stocks": results, "errors": errors})


@app.route("/stocks/<string:ticker>", methods=["GET"])
def get_stock(ticker: str):
    """Return pivot point data for a single stock."""
    ticker = ticker.upper()
    if ticker not in TOP_20_TICKERS:
        abort(404, description=f"Ticker '{ticker}' is not in the top-20 list.")
    try:
        payload = _build_stock_payload(ticker)
    except ValueError as exc:
        abort(404, description=str(exc))
    except Exception as exc:
        abort(500, description=str(exc))
    return jsonify(payload)


@app.route("/trade", methods=["POST"])
def execute_trade():
    """
    Execute a demo trade.

    Request body (JSON):
        { "ticker": "AAPL", "quantity": 5 }   -- quantity is optional, defaults to 1

    The action (BUY/SELL/HOLD) is determined automatically by the pivot-point
    signal for the current price.
    """
    data = request.get_json(silent=True) or {}
    ticker = (data.get("ticker") or "").upper()

    if not ticker:
        abort(400, description="'ticker' field is required.")
    if ticker not in TOP_20_TICKERS:
        abort(404, description=f"Ticker '{ticker}' is not in the top-20 list.")

    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        abort(400, description="'quantity' must be a positive integer.")

    try:
        ohlc = get_latest_ohlc(ticker)
        levels = calculate_pivot_points(ohlc["high"], ohlc["low"], ohlc["close"])
        action = trading_signal(ohlc["close"], levels)
        transaction = record_transaction(ticker, action, ohlc["close"], quantity)
    except ValueError as exc:
        abort(404, description=str(exc))
    except Exception as exc:
        abort(500, description=str(exc))

    return jsonify({
        "message": f"Demo trade executed: {action} {quantity} share(s) of {ticker} at ${ohlc['close']}",
        "transaction": transaction,
        "pivot_points": levels,
    }), 201


@app.route("/transactions", methods=["GET"])
def list_transactions():
    """Return all logged demo transactions."""
    return jsonify({"transactions": get_all_transactions()})


@app.route("/transactions/<string:ticker>", methods=["GET"])
def list_transactions_by_ticker(ticker: str):
    """Return demo transactions for a specific ticker."""
    return jsonify({"transactions": get_transactions_by_ticker(ticker.upper())})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(exc):
    return jsonify({"error": exc.description}), exc.code


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
