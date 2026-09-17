from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _u(uid):
    return f":{uid}" if uid else ""


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
                              style="danger")],
    ])


def games_main(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Куб", callback_data=f"game:dice{u}",
                              icon_custom_emoji_id="5321230889357713132"),
         InlineKeyboardButton(text="Футбол", callback_data=f"game:football{u}",
                              icon_custom_emoji_id="5319298377412812014"),
         InlineKeyboardButton(text="Баскет", callback_data=f"game:basketball{u}",
                              icon_custom_emoji_id="5318753363242820936")],
        [InlineKeyboardButton(text="Дартс", callback_data=f"game:darts{u}",
                              icon_custom_emoji_id="5319181640201706892"),
         InlineKeyboardButton(text="Боулинг", callback_data=f"game:bowling{u}",
                              icon_custom_emoji_id="5318753208623998230"),
         InlineKeyboardButton(text="Слоты", callback_data=f"game:slots{u}",
                              icon_custom_emoji_id="5321326856106976766")],
        [InlineKeyboardButton(text="Режимы", callback_data=f"game:modes{u}",
                              icon_custom_emoji_id="5309815458990433715"),
         InlineKeyboardButton(text="Авторские", callback_data=f"game:custom{u}",
                              icon_custom_emoji_id="5309815458990433715")],
        [InlineKeyboardButton(text="CatHome | NEWS", url="https://t.me/your_channel")],
    ])


def games_menu(uid=None):
    return games_main(uid)


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
        [InlineKeyboardButton(text="Лесенка (до x2)",
                              callback_data=f"d1:ladder1{u}"),
         InlineKeyboardButton(text="Лесенка (до x2.8)",
                              callback_data=f"d1:ladder2{u}")],
        [InlineKeyboardButton(text="💥 ВБ — весь баланс",
                              callback_data=f"d1:allin{u}", style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


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
        [InlineKeyboardButton(text="Любой дубль (x5.5)",
                              callback_data=f"d2:double{u}")],
        [InlineKeyboardButton(text="Сумма/Произв (до x17)",
                              callback_data=f"d2:sum_prod{u}")],
        [InlineKeyboardButton(text="Коридор (до x11)",
                              callback_data=f"d2:corridor{u}")],
        [InlineKeyboardButton(text="Снайпер (x3)",
                              callback_data=f"d2:sniper{u}"),
         InlineKeyboardButton(text="Лифт (x2.2)",
                              callback_data=f"d2:lift{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


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
        [InlineKeyboardButton(text="Любой трипл (x33)",
                              callback_data=f"d3:triple{u}")],
        [InlineKeyboardButton(text="Большой куб (x3.6)",
                              callback_data=f"d3:big{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def dice_menu(uid=None):       return dice_menu_1(uid)
def dice1_choices(uid=None):   return dice_menu_1(uid)
def dice2_choices(uid=None):   return dice_menu_2(uid)
def dice3_choices(uid=None):   return dice_menu_3(uid)


def football_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чистый гол (x4.7)", callback_data=f"fc:clean{u}"),
         InlineKeyboardButton(text="Любой гол (x2.5)", callback_data=f"fc:any{u}")],
        [InlineKeyboardButton(text="Застрял мяч (x4.7)", callback_data=f"fc:stuck{u}"),
         InlineKeyboardButton(text="Промах (x1.6)", callback_data=f"fc:miss{u}")],
        [InlineKeyboardButton(text="Выбор исходов (до x4.7)", callback_data=f"fc:multi{u}")],
        [InlineKeyboardButton(text="Дубль (до x23)", callback_data=f"fc:double{u}")],
        [InlineKeyboardButton(text="Снайпер (до x1.5)", callback_data=f"fc:sniper{u}")],
        [InlineKeyboardButton(text="Лесенка (до x2.8)", callback_data=f"fc:ladder{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def basketball_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр (x5.6)", callback_data=f"bc:center{u}"),
         InlineKeyboardButton(text="Красный (x1.9)", callback_data=f"bc:red{u}")],
        [InlineKeyboardButton(text="Белый (x2.8)", callback_data=f"bc:white{u}"),
         InlineKeyboardButton(text="Отскок (x5.6)", callback_data=f"bc:bounce{u}")],
        [InlineKeyboardButton(text="Выбор исходов (до x5.6)", callback_data=f"bc:multi{u}")],
        [InlineKeyboardButton(text="Дубль (до x33)", callback_data=f"bc:double{u}")],
        [InlineKeyboardButton(text="Лесенка (до x3.5)", callback_data=f"bc:ladder{u}"),
         InlineKeyboardButton(text="Оба попал (x1.3)", callback_data=f"bc:both{u}")],
        [InlineKeyboardButton(text="Две рядом (x2.5)", callback_data=f"bc:two_row{u}"),
         InlineKeyboardButton(text="Светофор (x2.7)", callback_data=f"bc:traffic{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def darts_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр (x4.7)", callback_data=f"dc:center{u}"),
         InlineKeyboardButton(text="Девятка (x4.7)", callback_data=f"dc:nine{u}")],
        [InlineKeyboardButton(text="Штанга (x2.5)", callback_data=f"dc:bar{u}"),
         InlineKeyboardButton(text="Промах (x2.5)", callback_data=f"dc:miss{u}")],
        [InlineKeyboardButton(text="Выбор исходов (до x4.7)", callback_data=f"dc:multi{u}")],
        [InlineKeyboardButton(text="Дубль (до x23)", callback_data=f"dc:double{u}")],
        [InlineKeyboardButton(text="Снайпер (до x1.5)", callback_data=f"dc:sniper{u}")],
        [InlineKeyboardButton(text="Лесенка (до x2.3)", callback_data=f"dc:ladder{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def bowling_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Страйк (x5.6)", callback_data=f"wc:strike{u}"),
         InlineKeyboardButton(text="Промах (x5.6)", callback_data=f"wc:miss{u}")],
        [InlineKeyboardButton(text="Выбор исходов (до x5.6)", callback_data=f"wc:multi{u}")],
        [InlineKeyboardButton(text="Дубль (до x33)", callback_data=f"wc:double{u}"),
         InlineKeyboardButton(text="Лесенка (до x3.5)", callback_data=f"wc:ladder{u}")],
        [InlineKeyboardButton(text="Сумма сбитых (до x8.1)", callback_data=f"wc:sum{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def slots_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="777 (x60)", callback_data=f"sl:777{u}"),
         InlineKeyboardButton(text="77* (x15)", callback_data=f"sl:77x{u}")],
        [InlineKeyboardButton(text="Любая комбинация (x15)", callback_data=f"sl:any{u}")],
        [InlineKeyboardButton(text="Лаки 7 (до x370)", callback_data=f"sl:lucky7{u}"),
         InlineKeyboardButton(text="Линии (до x150)", callback_data=f"sl:lines{u}")],
        [InlineKeyboardButton(text="Сумма (до x6)", callback_data=f"sl:sum{u}"),
         InlineKeyboardButton(text="Копилка (до x2.4)", callback_data=f"sl:piggy{u}")],
        [InlineKeyboardButton(text="Лесенка (до x27)", callback_data=f"sl:ladder{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def arcades_menu(uid=None):
    u = _u(uid)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mines", callback_data=f"ar:mines{u}"),
         InlineKeyboardButton(text="Dice", callback_data=f"ar:dice{u}")],
        [InlineKeyboardButton(text="Coinflip", callback_data=f"ar:coinflip{u}"),
         InlineKeyboardButton(text="Tower", callback_data=f"ar:tower{u}")],
        [InlineKeyboardButton(text="Рулетка", callback_data=f"ar:roulette{u}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"games_main{u}",
                              style="danger")],
    ])


def mines_count_menu(uid=None):
    u = _u(uid)
    rows, row = [], []
    for i in range(1, 25):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"mines_n:{i}{u}"))
        if len(row) == 6:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад", callback_data=f"game:custom{u}",
                                      style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
                              style="danger")],
    ])


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
        [InlineKeyboardButton(text="Назад", callback_data="deposit", style="danger")],
    ])


def withdraw_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CryptoBot", callback_data="wd:crypto",
                              icon_custom_emoji_id="5195058841988914267",
                              style="primary")],
        [InlineKeyboardButton(text="xRocket", callback_data="wd:xrocket",
                              icon_custom_emoji_id="5379612946747921985",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])


def referrals_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Вывести на баланс",
                              callback_data="ref:withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="success")],
        [InlineKeyboardButton(text="Моя ссылка", callback_data="ref:link",
                              icon_custom_emoji_id="5271604874419647061",
                              style="primary")],
        [InlineKeyboardButton(text="Топ", callback_data="ref:top",
                              icon_custom_emoji_id="5307942883314147223",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])


def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="primary")],
    ])


def currency_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Играть долларами", callback_data="cur:usd",
                              icon_custom_emoji_id="5197434882321567830",
                              style="success")],
        [InlineKeyboardButton(text="Отмена", callback_data="games_main",
                              style="danger")],
    ])


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
                              style="danger")],
    ])


def bet_currency_menu(): return currency_menu()
def bet_menu():          return quick_bet_menu()