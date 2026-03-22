"""
Pivot point calculation utilities.

Classic pivot point formula:
    Pivot (P) = (High + Low + Close) / 3
    Support 1  (S1) = (2 * P) - High
    Support 2  (S2) = P - (High - Low)
    Resistance 1 (R1) = (2 * P) - Low
    Resistance 2 (R2) = P + (High - Low)
"""


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    """
    Calculate classic pivot points, support, and resistance levels.

    :param high:  Highest price of the previous session
    :param low:   Lowest price of the previous session
    :param close: Closing price of the previous session
    :return: dict with keys pivot, s1, s2, r1, r2
    """
    pivot = (high + low + close) / 3
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)

    return {
        "pivot": round(pivot, 4),
        "s1": round(s1, 4),
        "s2": round(s2, 4),
        "r1": round(r1, 4),
        "r2": round(r2, 4),
    }


def trading_signal(current_price: float, levels: dict) -> str:
    """
    Determine a simple trading signal based on current price vs pivot levels.

    Rules:
        - BUY  : price is at or below S1 (near support)
        - SELL : price is at or above R1 (near resistance)
        - HOLD : price is between S1 and R1

    :param current_price: Latest market price
    :param levels: dict returned by calculate_pivot_points()
    :return: "BUY", "SELL", or "HOLD"
    """
    if current_price <= levels["s1"]:
        return "BUY"
    if current_price >= levels["r1"]:
        return "SELL"
    return "HOLD"
