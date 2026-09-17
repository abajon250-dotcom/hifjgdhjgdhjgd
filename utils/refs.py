from database import db

REF_PERCENT = 0.03


def give_ref_bonus(uid: int, win_amount: float) -> float:
    referrer = db.get_referrer(uid)
    if not referrer:
        return 0.0
    bonus = round(win_amount * REF_PERCENT, 2)
    if bonus <= 0:
        return 0.0
    db.add_ref_earnings(referrer, bonus)
    return bonus