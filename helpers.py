import requests
import os, re

from flask import redirect, session
from functools import wraps
from datetime import datetime, timedelta

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def brl(value):
    """Format value as BRL."""
    return f"R${value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def is_brazilian_numeric(value):
    # Regular expression to match Brazilian numeric format
    pattern = r'^\d+(,\d{1,2})?$'
    return bool(re.match(pattern, value))


# Utility to generate all months between the first and last entry
def generate_month_range(start_date, end_date):
    current = datetime.strptime(start_date, "%Y-%m")
    end = datetime.strptime(end_date, "%Y-%m")
    months = []
    while current <= end:
        months.append(current.strftime("%Y-%m"))
        current += timedelta(days=32)
        current = current.replace(day=1)
    return months