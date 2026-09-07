

"""
Breakpoint practice script.

A tiny order-processing pipeline. It runs without crashing
and prints a total. The total is wrong.

Do NOT read this file closely before doing the assignment.
Use the debugger to find things out.
"""

import random

random.seed(42)


def make_orders(n=200):
    """Build a list of order records. Some are messy."""
    orders = []
    for i in range(n):
        roll = random.random()
        if roll < 0.03:
            price = None                       # missing price
        elif roll < 0.08:
            price = f"{random.randint(1, 9)},{random.randint(100, 999)}"  # "1,234"
        elif roll < 0.11:
            price = -random.randint(1, 500)    # negative price
        else:
            price = random.randint(10, 2000)
        orders.append({
            "order_id": 1000 + i,
            "customer": f"cust_{random.randint(1, 25)}",
            "price": price,
            "qty": random.randint(1, 5),
        })
    return orders


def parse_price(value):
    """Turn a price into a number. Returns 0 if it can't."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def line_total(order):
    """Total for a single order line."""
    return parse_price(order["price"]) * order["qty"]


def summarize(orders):
    total = 0.0
    counted = 0
    for order in orders:
        amount = line_total(order)
        total += amount
        counted += 1
    return total, counted


if __name__ == "__main__":
    orders = make_orders()
    total, counted = summarize(orders)
    print(f"Processed {counted} orders")
    print(f"Total revenue: {total:,.2f}")