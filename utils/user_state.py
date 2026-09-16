from database import db

DEFAULT_BET = 0.5
DEFAULT_CURRENCY = "usd"


def get_state(user_id: int) -> dict:
    return {
        "currency": db.get_bet_currency(user_id),
        "bet": db.get_bet(user_id),
    }


def get_bet(user_id: int) -> float:
    return db.get_bet(user_id)


def get_currency(user_id: int) -> str:
    return db.get_bet_currency(user_id)


def set_bet(user_id: int, bet: float):
    db.set_bet(user_id, float(bet))


def set_currency(user_id: int, currency: str):
    db.set_bet_currency(user_id, currency)