from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _u(uid):
    return f":{uid}" if uid else ""


# ============================================================
#                    ГЛАВНОЕ МЕНЮ
# ============================================================
def main_menu_inline(is_admin: bool = False):
    rows = [
        [InlineKeyboardButton(text="Профиль", callback_data="profile",
                              icon_custom_emoji_id="5308004189677330658",
                              style="primary"),
         InlineKeyboardButton(text="Игры", callback_data="games_main",
                              icon_custom_emoji_id="5309815458990433715",
                              style="success")],
        [InlineKeyboardButton(text="Статистика", callback_data="stats",
                              icon_custom_emoji_id="5231200819986047254",
                              style="primary"),
         InlineKeyboardButton(text="Бонусы", callback_data="bonuses",
                              icon_custom_emoji_id="5307603391919204061",
                              style="success")],
        [InlineKeyboardButton(text="Рефералы", callback_data="referrals",
                              icon_custom_emoji_id="5395732581780040886",
                              style="primary"),
         InlineKeyboardButton(text="Приватность", callback_data="privacy",
                              icon_custom_emoji_id="5197288647275071607")],
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit",
                              icon_custom_emoji_id="5445355530111437729",
                              style="success"),
         InlineKeyboardButton(text="Вывести", callback_data="withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="danger")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="👑 Админ-панель",
                                          callback_data="admin_panel",
                                          style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def balance_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit",
                              icon_custom_emoji_id="5445355530111437729",
                              style="success"),
         InlineKeyboardButton(text="Вывести", callback_data="withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")]])


# ============================================================
#                    МЕНЮ ИГР
# ============================================================
def games_main(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Куб", callback_data=f"game:dice{u}"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data=f"game:football{u}"),
         InlineKeyboardButton(text="🏀 Баскет", callback_data=f"game:basketball{u}")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data=f"game:darts{u}"),
         InlineKeyboardButton(text="🎳 Боулинг", callback_data=f"game:bowling{u}"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data=f"game:slots{u}")],
        [InlineKeyboardButton(text="💣 Мины", callback_data=f"game:mines{u}"),
         InlineKeyboardButton(text="🏰 Башня", callback_data=f"game:tower{u}")],
        [InlineKeyboardButton(text="🚀 Краш", callback_data=f"game:crash{u}"),
         InlineKeyboardButton(text="🎯 Кено", callback_data=f"game:keno{u}"),
         InlineKeyboardButton(text="🎡 Рулетка", callback_data=f"game:roulette{u}")],
        [InlineKeyboardButton(text="CatHome | NEWS", url="https://t.me/your_channel")],
    ])


def games_menu(uid=None):
    return games_main(uid)


# ============================================================
#                    КУБИКИ
# ============================================================
def _dice_tabs(active: int, uid=None):
    u = _u(uid)
    return [
        InlineKeyboardButton(text="1 куб", callback_data=f"dice:1{u}",
                             style="success" if active == 1 else "primary"),
        InlineKeyboardButton(text="2 куба", callback_data=f"dice:2{u}",
                             style="success" if active == 2 else "primary"),
        InlineKeyboardButton(text="3 куба", callback_data=f"dice:3{u}",
                             style="success" if active == 3 else "primary"),
    ]


def dice_menu_1(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(1, uid),
        [InlineKeyboardButton(text="Чёт (x1.9)", callback_data=f"d1:even{u}"),
         InlineKeyboardButton(text="Нечёт (x1.9)", callback_data=f"d1:odd{u}")],
        [InlineKeyboardButton(text="Меньше (x1.9)", callback_data=f"d1:less{u}"),
         InlineKeyboardButton(text="Больше (x1.9)", callback_data=f"d1:more{u}")],
        [InlineKeyboardButton(text="1 (x5.6)", callback_data=f"d1:num1{u}"),
         InlineKeyboardButton(text="2 (x5.6)", callback_data=f"d1:num2{u}"),
         InlineKeyboardButton(text="3 (x5.6)", callback_data=f"d1:num3{u}")],
        [InlineKeyboardButton(text="4 (x5.6)", callback_data=f"d1:num4{u}"),
         InlineKeyboardButton(text="5 (x5.6)", callback_data=f"d1:num5{u}"),
         InlineKeyboardButton(text="6 (x5.6)", callback_data=f"d1:num6{u}")],
        [InlineKeyboardButton(text="Не 6 (1-5 → x3-7, 6 → -18x)",
                              callback_data=f"d1:no_6{u}")],
        [InlineKeyboardButton(text="Числа (до x2.8)",
                              callback_data=f"d1:numbers{u}"),
         InlineKeyboardButton(text="Без чисел (до x5.6)",
                              callback_data=f"d1:no_numbers{u}")],
        [InlineKeyboardButton(text="💥 ВБ — весь баланс",
                              callback_data=f"d1:allin{u}", style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


def dice_menu_2(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(2, uid),
        [InlineKeyboardButton(text="Чёт (x3.8)", callback_data=f"d2:even{u}"),
         InlineKeyboardButton(text="Нечёт (x3.8)", callback_data=f"d2:odd{u}")],
        [InlineKeyboardButton(text="Больше (x3.8)", callback_data=f"d2:more{u}"),
         InlineKeyboardButton(text="Меньше (x3.8)", callback_data=f"d2:less{u}")],
        [InlineKeyboardButton(text="1 (x33)", callback_data=f"d2:num1{u}"),
         InlineKeyboardButton(text="2 (x33)", callback_data=f"d2:num2{u}"),
         InlineKeyboardButton(text="3 (x33)", callback_data=f"d2:num3{u}")],
        [InlineKeyboardButton(text="4 (x33)", callback_data=f"d2:num4{u}"),
         InlineKeyboardButton(text="5 (x33)", callback_data=f"d2:num5{u}"),
         InlineKeyboardButton(text="6 (x33)", callback_data=f"d2:num6{u}")],
        [InlineKeyboardButton(text="Дубль (x5.5)", callback_data=f"d2:double{u}")],
        [InlineKeyboardButton(text="Сумма/Произв (до x17)",
                              callback_data=f"d2:sum_prod{u}")],
        [InlineKeyboardButton(text="Коридор (до x11)",
                              callback_data=f"d2:corridor{u}")],
        [InlineKeyboardButton(text="Снайпер (x3)", callback_data=f"d2:sniper{u}"),
         InlineKeyboardButton(text="Лифт (x2.2)", callback_data=f"d2:lift{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


def dice_menu_3(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(3, uid),
        [InlineKeyboardButton(text="Чёт (x7.5)", callback_data=f"d3:even{u}"),
         InlineKeyboardButton(text="Нечёт (x7.5)", callback_data=f"d3:odd{u}")],
        [InlineKeyboardButton(text="Больше (x7.5)", callback_data=f"d3:more{u}"),
         InlineKeyboardButton(text="Меньше (x7.5)", callback_data=f"d3:less{u}")],
        [InlineKeyboardButton(text="1 (x200)", callback_data=f"d3:num1{u}"),
         InlineKeyboardButton(text="2 (x200)", callback_data=f"d3:num2{u}"),
         InlineKeyboardButton(text="3 (x200)", callback_data=f"d3:num3{u}")],
        [InlineKeyboardButton(text="4 (x200)", callback_data=f"d3:num4{u}"),
         InlineKeyboardButton(text="5 (x200)", callback_data=f"d3:num5{u}"),
         InlineKeyboardButton(text="6 (x200)", callback_data=f"d3:num6{u}")],
        [InlineKeyboardButton(text="Трипл (x33)", callback_data=f"d3:triple{u}")],
        [InlineKeyboardButton(text="Большой куб (x3.6)", callback_data=f"d3:big{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


def dice_menu(uid=None):       return dice_menu_1(uid)
def dice1_choices(uid=None):   return dice_menu_1(uid)
def dice2_choices(uid=None):   return dice_menu_2(uid)
def dice3_choices(uid=None):   return dice_menu_3(uid)


# ============================================================
#                    ФУТБОЛ
# ============================================================
def football_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Мимо ворот (x5.5)", callback_data=f"fc:mimo{u}"),
         InlineKeyboardButton(text="🥅 В штангу (x5.5)", callback_data=f"fc:shtanga{u}")],
        [InlineKeyboardButton(text="🧱 Застрял мяч (x5.5)", callback_data=f"fc:zastryal{u}"),
         InlineKeyboardButton(text="⚽ Гол от штанги (x5.5)", callback_data=f"fc:from_shtanga{u}")],
        [InlineKeyboardButton(text="⚽ Чистый гол в центр (x5.5)", callback_data=f"fc:center{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


# ============================================================
#                    БАСКЕТ
# ============================================================
def basketball_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Отскок (x5.5)", callback_data=f"bc:otskok{u}"),
         InlineKeyboardButton(text="🏀 С краем (x5.5)", callback_data=f"bc:edge{u}")],
        [InlineKeyboardButton(text="🏀 Застрял (x5.5)", callback_data=f"bc:zastryal{u}"),
         InlineKeyboardButton(text="🏀 Близко (x5.5)", callback_data=f"bc:blizko{u}")],
        [InlineKeyboardButton(text="🏀 Прямое попадание (x5.5)", callback_data=f"bc:direct{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


# ============================================================
#                    ДАРТС
# ============================================================
def darts_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Промах (x5.5)", callback_data=f"dc:miss{u}"),
         InlineKeyboardButton(text="🎯 В центр (x5.5)", callback_data=f"dc:bull{u}")],
        [InlineKeyboardButton(text="🎯 Сектор 1 (x5.5)", callback_data=f"dc:s1{u}"),
         InlineKeyboardButton(text="🎯 Сектор 2 (x5.5)", callback_data=f"dc:s2{u}")],
        [InlineKeyboardButton(text="🎯 Сектор 3 (x5.5)", callback_data=f"dc:s3{u}"),
         InlineKeyboardButton(text="🎯 Сектор 4 (x5.5)", callback_data=f"dc:s4{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


# ============================================================
#                    БОУЛИНГ
# ============================================================
def bowling_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎳 Промах (x5.5)", callback_data=f"wc:miss{u}"),
         InlineKeyboardButton(text="🎳 Сбито 1/6 (x5.5)", callback_data=f"wc:p1{u}")],
        [InlineKeyboardButton(text="🎳 Сбито 3/6 (x5.5)", callback_data=f"wc:p3{u}"),
         InlineKeyboardButton(text="🎳 Сбито 4/6 (x5.5)", callback_data=f"wc:p4{u}")],
        [InlineKeyboardButton(text="🎳 Сбито 5/6 (x5.5)", callback_data=f"wc:p5{u}"),
         InlineKeyboardButton(text="🎳 Страйк (x5.5)", callback_data=f"wc:strike{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


# ============================================================
#                    СЛОТЫ
# ============================================================
def slots_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Трипл (x60)", callback_data=f"sl:triple{u}"),
         InlineKeyboardButton(text="✌️ Дубль (x15)", callback_data=f"sl:double{u}")],
        [InlineKeyboardButton(text="7️⃣ Одна 7 (x3)", callback_data=f"sl:one{u}")],
        [InlineKeyboardButton(text="💎 3×7 (x100)", callback_data=f"sl:exact{u}")],
        [InlineKeyboardButton(text="🔀 Уникальные (x2)", callback_data=f"sl:unique{u}")],
        [InlineKeyboardButton(text="💥 7+BAR (x20)", callback_data=f"sl:combo{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")]])


# ============================================================
#                    МИНЫ
# ============================================================
def mines_count_menu(uid=None):
    u = _u(uid)
    rows, row = [], []
    for i in range(1, 25):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"mines_n:{i}{u}"))
        if len(row) == 6:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                                      style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ============================================================
#                    ДЕПОЗИТ / ВЫВОД
# ============================================================
def deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CryptoBot", callback_data="dep:crypto",
                              icon_custom_emoji_id="5195058841988914267",
                              style="primary")],
        [InlineKeyboardButton(text="xRocket", callback_data="dep:xrocket",
                              icon_custom_emoji_id="5379612946747921985",
                              style="primary")],
        [InlineKeyboardButton(text="Telegram Stars", callback_data="dep:stars",
                              icon_custom_emoji_id="5895708410447401643",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")]])


def deposit_amounts(method):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0.5 USDT", callback_data=f"depamt:{method}:0.5"),
         InlineKeyboardButton(text="1 USDT", callback_data=f"depamt:{method}:1")],
        [InlineKeyboardButton(text="5 USDT", callback_data=f"depamt:{method}:5"),
         InlineKeyboardButton(text="10 USDT", callback_data=f"depamt:{method}:10")],
        [InlineKeyboardButton(text="25 USDT", callback_data=f"depamt:{method}:25"),
         InlineKeyboardButton(text="50 USDT", callback_data=f"depamt:{method}:50")],
        [InlineKeyboardButton(text="Своя сумма", callback_data=f"depcustom:{method}",
                              style="success")],
        [InlineKeyboardButton(text="Назад", callback_data="deposit", style="danger")]])


def withdraw_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CryptoBot", callback_data="wd:crypto",
                              icon_custom_emoji_id="5195058841988914267",
                              style="primary")],
        [InlineKeyboardButton(text="xRocket", callback_data="wd:xrocket",
                              icon_custom_emoji_id="5379612946747921985",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")]])


# ============================================================
#                    РЕФЕРАЛЫ / BACK
# ============================================================
def referrals_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Вывести на баланс",
                              callback_data="ref:withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="success")],
        [InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="ref:link",
                              icon_custom_emoji_id="5271604874419647061",
                              style="primary"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="ref:top",
                              icon_custom_emoji_id="5307942883314147223",
                              style="primary")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="ref:promo_help",
                              style="success"),
         InlineKeyboardButton(text="🧾 Чек", callback_data="ref:check_help",
                              style="success")],
        [InlineKeyboardButton(text="📢 Мой чат", callback_data="ref:chat_help",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")]])


def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="primary")]])


def currency_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Играть долларами", callback_data="cur:usd",
                              icon_custom_emoji_id="5197434882321567830",
                              style="success")],
        [InlineKeyboardButton(text="Отмена", callback_data="games_main",
                              style="danger")]])


def quick_bet_menu(currency: str = "usd"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0.5", callback_data="qb:0.5"),
         InlineKeyboardButton(text="1", callback_data="qb:1"),
         InlineKeyboardButton(text="5", callback_data="qb:5")],
        [InlineKeyboardButton(text="10", callback_data="qb:10"),
         InlineKeyboardButton(text="50", callback_data="qb:50")],
        [InlineKeyboardButton(text="Своя ставка", callback_data="qb:custom",
                              style="success")],
        [InlineKeyboardButton(text="Отмена", callback_data="games_main",
                              style="danger")]])


def bet_currency_menu(): return currency_menu()
def bet_menu():          return quick_bet_menu()