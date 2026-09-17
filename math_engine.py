import os
import random
from dotenv import load_dotenv

load_dotenv()

HOUSE_EDGE = float(os.getenv("HOUSE_EDGE", 0.05))
COMMISSION_DEPOSIT = 0.05
COMMISSION_WITHDRAW = 0.0
STARS_TO_USD = 0.013

MIN_DEPOSIT = 0.2
MIN_WITHDRAW = 1.0
WIN_COMMISSION = 0.10


def stars_to_usd(stars): return round(stars * STARS_TO_USD, 2)
def usd_to_stars(usd):   return round(usd / STARS_TO_USD, 2)


def apply_deposit_commission(a):
    return round(a - a * COMMISSION_DEPOSIT, 2), round(a * COMMISSION_DEPOSIT, 2)


def apply_withdraw_commission(a):
    return round(a - a * COMMISSION_WITHDRAW, 2), round(a * COMMISSION_WITHDRAW, 2)


def apply_win_commission(win):
    if win <= 0:
        return 0.0, 0.0
    commission = round(win * WIN_COMMISSION, 2)
    return round(win - commission, 2), commission


def calc_1_dice(bet, choice, v):
    win, result = 0.0, "lose"
    if choice == "even" and v % 2 == 0: win, result = bet * 1.9, "win"
    elif choice == "odd" and v % 2 != 0: win, result = bet * 1.9, "win"
    elif choice == "less" and v <= 3: win, result = bet * 1.9, "win"
    elif choice == "more" and v >= 4: win, result = bet * 1.9, "win"
    elif choice.startswith("num") and v == int(choice[3:]): win, result = bet * 5.6, "win"
    elif choice == "numbers" and v in (3, 4): win, result = bet * 2.8, "win"
    elif choice == "no_numbers" and v in (1, 6): win, result = bet * 5.6, "win"
    elif choice == "ladder1" and v in (1, 2): win, result = bet * 2.0, "win"
    elif choice == "ladder2" and v in (5, 6): win, result = bet * 2.8, "win"
    elif choice == "no_6":
        if v == 6: win, result = -bet * 18, "lose"
        else:
            mult = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}[v]
            win, result = bet * mult, "win"
    return round(win, 2), result


def calc_2_dice(bet, choice, d1, d2):
    win, result = 0.0, "lose"
    both_even = d1 % 2 == 0 and d2 % 2 == 0
    both_odd  = d1 % 2 == 1 and d2 % 2 == 1
    both_high = d1 >= 4 and d2 >= 4
    both_low  = d1 <= 3 and d2 <= 3
    if choice == "even" and both_even: win, result = bet * 3.8, "win"
    elif choice == "odd" and both_odd: win, result = bet * 3.8, "win"
    elif choice == "more" and both_high: win, result = bet * 3.8, "win"
    elif choice == "less" and both_low: win, result = bet * 3.8, "win"
    elif choice.startswith("num"):
        n = int(choice[3:])
        if d1 == n and d2 == n: win, result = bet * 33, "win"
    elif choice == "double" and d1 == d2: win, result = bet * 5.5, "win"
    elif choice == "sum_prod":
        if (d1 + d2) == 10 or (d1 * d2) == 10: win, result = bet * 17, "win"
    elif choice == "corridor" and 5 <= (d1 + d2) <= 9: win, result = bet * 11, "win"
    elif choice == "sniper" and d1 == d2 == 6: win, result = bet * 3, "win"
    elif choice == "lift" and (d1 + d2) >= 10: win, result = bet * 2.2, "win"
    elif choice == "sum7_exact" and (d1 + d2) == 7: win, result = bet * 5.5, "win"
    elif choice == "sum7_less" and (d1 + d2) < 7: win, result = bet * 2.5, "win"
    elif choice == "sum7_greater" and (d1 + d2) > 7: win, result = bet * 2.5, "win"
    return round(win, 2), result


def calc_3_dice(bet, choice, d1, d2, d3):
    dice = [d1, d2, d3]
    win, result = 0.0, "lose"
    all_even = all(d % 2 == 0 for d in dice)
    all_odd  = all(d % 2 == 1 for d in dice)
    all_high = all(d >= 4 for d in dice)
    all_low  = all(d <= 3 for d in dice)
    if choice == "even" and all_even: win, result = bet * 7.5, "win"
    elif choice == "odd" and all_odd: win, result = bet * 7.5, "win"
    elif choice == "more" and all_high: win, result = bet * 7.5, "win"
    elif choice == "less" and all_low: win, result = bet * 7.5, "win"
    elif choice.startswith("num"):
        n = int(choice[3:])
        if all(d == n for d in dice): win, result = bet * 200, "win"
    elif choice == "triple" and len(set(dice)) == 1: win, result = bet * 33, "win"
    elif choice == "big" and max(dice) >= 6: win, result = bet * 3.6, "win"
    return round(win, 2), result


def calc_football(bet, choice, v):
    if choice == "clean" and v == 5: return round(bet * 4.7, 2), "win"
    if choice == "any" and v in (3, 4, 5): return round(bet * 2.5, 2), "win"
    if choice == "stuck" and v == 3: return round(bet * 4.7, 2), "win"
    if choice == "miss" and v in (1, 2): return round(bet * 1.6, 2), "win"
    if choice == "multi" and v in (3, 4): return round(bet * 4.7, 2), "win"
    if choice == "double" and v == 5: return round(bet * 23, 2), "win"
    if choice == "sniper" and v == 5: return round(bet * 1.5, 2), "win"
    if choice == "ladder" and v in (4, 5): return round(bet * 2.8, 2), "win"
    return 0.0, "lose"


def calc_basketball(bet, choice, v):
    if choice == "center" and v == 5: return round(bet * 5.6, 2), "win"
    if choice == "red" and v == 1: return round(bet * 1.9, 2), "win"
    if choice == "white" and v == 2: return round(bet * 2.8, 2), "win"
    if choice == "bounce" and v == 1: return round(bet * 5.6, 2), "win"
    if choice == "multi" and v == 4: return round(bet * 5.6, 2), "win"
    if choice == "double" and v == 5: return round(bet * 33, 2), "win"
    if choice == "ladder" and v in (3, 4): return round(bet * 3.5, 2), "win"
    if choice == "both" and v == 5: return round(bet * 1.3, 2), "win"
    if choice == "two_row" and v in (2, 3): return round(bet * 2.5, 2), "win"
    if choice == "traffic" and v == 4: return round(bet * 2.7, 2), "win"
    return 0.0, "lose"


def calc_darts(bet, choice, v):
    if choice == "center" and v == 2: return round(bet * 4.7, 2), "win"
    if choice == "nine" and v == 6: return round(bet * 4.7, 2), "win"
    if choice == "bar" and v == 5: return round(bet * 2.5, 2), "win"
    if choice == "miss" and v == 1: return round(bet * 2.5, 2), "win"
    if choice == "multi" and v in (3, 4): return round(bet * 4.7, 2), "win"
    if choice == "double" and v == 2: return round(bet * 23, 2), "win"
    if choice == "sniper" and v == 2: return round(bet * 1.5, 2), "win"
    if choice == "ladder" and v in (4, 5): return round(bet * 2.3, 2), "win"
    return 0.0, "lose"


def calc_bowling(bet, choice, v):
    if choice == "strike" and v == 6: return round(bet * 5.6, 2), "win"
    if choice == "miss" and v == 1: return round(bet * 5.6, 2), "win"
    if choice == "multi" and v in (4, 5): return round(bet * 5.6, 2), "win"
    if choice == "double" and v == 6: return round(bet * 33, 2), "win"
    if choice == "ladder" and v in (4, 5, 6): return round(bet * 3.5, 2), "win"
    if choice == "sum" and v >= 4: return round(bet * 8.1, 2), "win"
    return 0.0, "lose"


SLOT_SYMBOLS = ["7️⃣", "🍇", "🍋", "BAR", "🔔", "💎"]


def spin_slots():
    return [random.choice(SLOT_SYMBOLS) for _ in range(3)]


def calc_slots(bet, choice, reels):
    win, result = 0.0, "lose"
    if choice == "777" and reels == ["7️⃣", "7️⃣", "7️⃣"]: win, result = bet * 60, "win"
    elif choice == "77x" and reels[0] == reels[1] == "7️⃣": win, result = bet * 15, "win"
    elif choice == "any" and len(set(reels)) == 1: win, result = bet * 15, "win"
    elif choice == "lucky7" and "7️⃣" in reels: win, result = bet * 370, "win"
    elif choice == "lines" and len(set(reels)) <= 2: win, result = bet * 150, "win"
    elif choice == "sum": win, result = bet * 6, "win" if random.random() < 0.4 else "lose"
    elif choice == "piggy": win, result = bet * 2.4, "win" if random.random() < 0.5 else "lose"
    elif choice == "ladder" and len(set(reels)) == 1: win, result = bet * 27, "win"
    return round(win, 2), result


def mines_multiplier(mines, opened, total=25):
    if opened == 0: return 1.0
    safe = total - mines
    try:
        prob = 1.0
        for i in range(opened): prob *= (safe - i) / (total - i)
        return round((1.0 / prob) * (1 - HOUSE_EDGE), 2)
    except Exception:
        return round(1.0 + opened * 0.1 * mines, 2)


def tower_multiplier(level, difficulty="easy"):
    base = {"easy": 1.5, "medium": 2.0, "hard": 3.0, "extreme": 5.0}.get(difficulty, 1.5)
    m = 1.0
    for _ in range(level): m *= base
    return round(m * (1 - HOUSE_EDGE), 2)


def generate_crash_point():
    r = random.random()
    if r < 0.05: return 1.0
    return round(max(1.0, (1 / (1 - r)) * 0.95), 2)


def keno_multiplier(hits, picks):
    table = {(10, 10): 100.0, (10, 9): 20.0, (10, 8): 5.0,
             (8, 8): 50.0, (8, 7): 10.0, (5, 5): 20.0, (5, 4): 5.0, (3, 3): 10.0}
    return round(table.get((picks, hits), 0.0) * (1 - HOUSE_EDGE), 2)


def roulette_multiplier(bet, choice, number, color):
    if choice == color:
        if color == "green": return round(bet * 14, 2), "win"
        return round(bet * 2, 2), "win"
    if choice == "even" and number % 2 == 0 and number != 0: return round(bet * 2, 2), "win"
    if choice == "odd" and number % 2 != 0: return round(bet * 2, 2), "win"
    return 0.0, "lose"