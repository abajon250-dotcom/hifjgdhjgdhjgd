from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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


# ============================================================
#                    КОШЕЛЁК
# ============================================================
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


# ============================================================
#                    МЕНЮ ИГР
# ============================================================
def games_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Куб", callback_data="game:dice",
                              icon_custom_emoji_id="5321230889357713132"),
         InlineKeyboardButton(text="Футбол", callback_data="game:football",
                              icon_custom_emoji_id="5319298377412812014"),
         InlineKeyboardButton(text="Баскет", callback_data="game:basketball",
                              icon_custom_emoji_id="5318753363242820936")],
        [InlineKeyboardButton(text="Дартс", callback_data="game:darts",
                              icon_custom_emoji_id="5319181640201706892"),
         InlineKeyboardButton(text="Боулинг", callback_data="game:bowling",
                              icon_custom_emoji_id="5318753208623998230"),
         InlineKeyboardButton(text="Слоты", callback_data="game:slots",
                              icon_custom_emoji_id="5321326856106976766")],
        [InlineKeyboardButton(text="Режимы", callback_data="game:modes",
                              icon_custom_emoji_id="5309815458990433715"),
         InlineKeyboardButton(text="Авторские", callback_data="game:custom",
                              icon_custom_emoji_id="5309815458990433715")],
        [InlineKeyboardButton(text="CatHome | NEWS", url="https://t.me/your_channel")],
    ])


def games_menu():
    return games_main()


# ============================================================
#                    КУБИКИ
# ============================================================
def _dice_tabs(active: int):
    return [
        InlineKeyboardButton(text="1 куб", callback_data="dice:1",
                             style="success" if active == 1 else "primary"),
        InlineKeyboardButton(text="2 куба", callback_data="dice:2",
                             style="success" if active == 2 else "primary"),
        InlineKeyboardButton(text="3 куба", callback_data="dice:3",
                             style="success" if active == 3 else "primary"),
    ]


def dice_menu_1():
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(1),
        [InlineKeyboardButton(text="Чёт (x1.9)", callback_data="d1:even"),
         InlineKeyboardButton(text="Нечёт (x1.9)", callback_data="d1:odd")],
        [InlineKeyboardButton(text="Меньше (x1.9)", callback_data="d1:less"),
         InlineKeyboardButton(text="Больше (x1.9)", callback_data="d1:more")],
        [InlineKeyboardButton(text="1 (x5.6)", callback_data="d1:num1"),
         InlineKeyboardButton(text="2 (x5.6)", callback_data="d1:num2"),
         InlineKeyboardButton(text="3 (x5.6)", callback_data="d1:num3")],
        [InlineKeyboardButton(text="4 (x5.6)", callback_data="d1:num4"),
         InlineKeyboardButton(text="5 (x5.6)", callback_data="d1:num5"),
         InlineKeyboardButton(text="6 (x5.6)", callback_data="d1:num6")],
        [InlineKeyboardButton(text="Числа (до x2.8)", callback_data="d1:numbers"),
         InlineKeyboardButton(text="Без чисел (до x5.6)", callback_data="d1:no_numbers")],
        [InlineKeyboardButton(text="Лесенка (до x2)", callback_data="d1:ladder1"),
         InlineKeyboardButton(text="Лесенка (до x2.8)", callback_data="d1:ladder2")],
        [InlineKeyboardButton(text="💥 ВБ — весь баланс",
                              callback_data="d1:allin", style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def dice_menu_2():
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(2),
        [InlineKeyboardButton(text="Чёт (x3.8)", callback_data="d2:even"),
         InlineKeyboardButton(text="Нечёт (x3.8)", callback_data="d2:odd")],
        [InlineKeyboardButton(text="Больше (x3.8)", callback_data="d2:more"),
         InlineKeyboardButton(text="Меньше (x3.8)", callback_data="d2:less")],
        [InlineKeyboardButton(text="1 (x33)", callback_data="d2:num1"),
         InlineKeyboardButton(text="2 (x33)", callback_data="d2:num2"),
         InlineKeyboardButton(text="3 (x33)", callback_data="d2:num3")],
        [InlineKeyboardButton(text="4 (x33)", callback_data="d2:num4"),
         InlineKeyboardButton(text="5 (x33)", callback_data="d2:num5"),
         InlineKeyboardButton(text="6 (x33)", callback_data="d2:num6")],
        [InlineKeyboardButton(text="Любой дубль (x5.5)", callback_data="d2:double")],
        [InlineKeyboardButton(text="Сумма/Произведение (до x17)",
                              callback_data="d2:sum_prod")],
        [InlineKeyboardButton(text="Коридор (до x11)", callback_data="d2:corridor")],
        [InlineKeyboardButton(text="Снайпер (x3)", callback_data="d2:sniper"),
         InlineKeyboardButton(text="Лифт (x2.2)", callback_data="d2:lift")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def dice_menu_3():
    return InlineKeyboardMarkup(inline_keyboard=[
        _dice_tabs(3),
        [InlineKeyboardButton(text="Чёт (x7.5)", callback_data="d3:even"),
         InlineKeyboardButton(text="Нечёт (x7.5)", callback_data="d3:odd")],
        [InlineKeyboardButton(text="Больше (x7.5)", callback_data="d3:more"),
         InlineKeyboardButton(text="Меньше (x7.5)", callback_data="d3:less")],
        [InlineKeyboardButton(text="1 (x200)", callback_data="d3:num1"),
         InlineKeyboardButton(text="2 (x200)", callback_data="d3:num2"),
         InlineKeyboardButton(text="3 (x200)", callback_data="d3:num3")],
        [InlineKeyboardButton(text="4 (x200)", callback_data="d3:num4"),
         InlineKeyboardButton(text="5 (x200)", callback_data="d3:num5"),
         InlineKeyboardButton(text="6 (x200)", callback_data="d3:num6")],
        [InlineKeyboardButton(text="Любой трипл (x33)", callback_data="d3:triple")],
        [InlineKeyboardButton(text="Большой куб (x3.6)", callback_data="d3:big")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def dice_menu():       return dice_menu_1()
def dice1_choices():   return dice_menu_1()
def dice2_choices():   return dice_menu_2()
def dice3_choices():   return dice_menu_3()


# ============================================================
#                    СПОРТ
# ============================================================
def football_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чистый гол (x4.7)", callback_data="fc:clean"),
         InlineKeyboardButton(text="Любой гол (x2.5)", callback_data="fc:any")],
        [InlineKeyboardButton(text="Застрял мяч (x4.7)", callback_data="fc:stuck"),
         InlineKeyboardButton(text="Промах (x1.6)", callback_data="fc:miss")],
        [InlineKeyboardButton(text="Выбор исходов (до x4.7)", callback_data="fc:multi")],
        [InlineKeyboardButton(text="Дубль (до x23)", callback_data="fc:double")],
        [InlineKeyboardButton(text="Снайпер (до x1.5)", callback_data="fc:sniper")],
        [InlineKeyboardButton(text="Лесенка (до x2.8)", callback_data="fc:ladder")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def basketball_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр (x5.6)", callback_data="bc:center"),
         InlineKeyboardButton(text="Красный (x1.9)", callback_data="bc:red")],
        [InlineKeyboardButton(text="Белый (x2.8)", callback_data="bc:white"),
         InlineKeyboardButton(text="Отскок (x5.6)", callback_data="bc:bounce")],
        [InlineKeyboardButton(text="Выбор исходов (до x5.6)", callback_data="bc:multi")],
        [InlineKeyboardButton(text="Дубль (до x33)", callback_data="bc:double")],
        [InlineKeyboardButton(text="Лесенка (до x3.5)", callback_data="bc:ladder"),
         InlineKeyboardButton(text="Оба попал (x1.3)", callback_data="bc:both")],
        [InlineKeyboardButton(text="Две рядом (x2.5)", callback_data="bc:two_row"),
         InlineKeyboardButton(text="Светофор (x2.7)", callback_data="bc:traffic")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def darts_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Центр (x4.7)", callback_data="dc:center"),
         InlineKeyboardButton(text="Девятка (x4.7)", callback_data="dc:nine")],
        [InlineKeyboardButton(text="Штанга (x2.5)", callback_data="dc:bar"),
         InlineKeyboardButton(text="Промах (x2.5)", callback_data="dc:miss")],
        [InlineKeyboardButton(text="Выбор исходов (до x4.7)", callback_data="dc:multi")],
        [InlineKeyboardButton(text="Дубль (до x23)", callback_data="dc:double")],
        [InlineKeyboardButton(text="Снайпер (до x1.5)", callback_data="dc:sniper")],
        [InlineKeyboardButton(text="Лесенка (до x2.3)", callback_data="dc:ladder")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def bowling_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Страйк (x5.6)", callback_data="wc:strike"),
         InlineKeyboardButton(text="Промах (x5.6)", callback_data="wc:miss")],
        [InlineKeyboardButton(text="Выбор исходов (до x5.6)", callback_data="wc:multi")],
        [InlineKeyboardButton(text="Дубль (до x33)", callback_data="wc:double"),
         InlineKeyboardButton(text="Лесенка (до x3.5)", callback_data="wc:ladder")],
        [InlineKeyboardButton(text="Сумма сбитых (до x8.1)", callback_data="wc:sum")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


# ============================================================
#                    СЛОТЫ
# ============================================================
def slots_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="777 (x60)", callback_data="sl:777"),
         InlineKeyboardButton(text="77* (x15)", callback_data="sl:77x")],
        [InlineKeyboardButton(text="Любая комбинация (x15)", callback_data="sl:any")],
        [InlineKeyboardButton(text="Лаки 7 (до x370)", callback_data="sl:lucky7"),
         InlineKeyboardButton(text="Линии (до x150)", callback_data="sl:lines")],
        [InlineKeyboardButton(text="Сумма (до x6)", callback_data="sl:sum"),
         InlineKeyboardButton(text="Копилка (до x2.4)", callback_data="sl:piggy")],
        [InlineKeyboardButton(text="Лесенка (до x27)", callback_data="sl:ladder")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


# ============================================================
#                    АРКАДЫ
# ============================================================
def arcades_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mines", callback_data="ar:mines"),
         InlineKeyboardButton(text="Dice", callback_data="ar:dice")],
        [InlineKeyboardButton(text="Coinflip", callback_data="ar:coinflip"),
         InlineKeyboardButton(text="Tower", callback_data="ar:tower")],
        [InlineKeyboardButton(text="Рулетка", callback_data="ar:roulette")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])


def mines_count_menu():
    rows, row = [], []
    for i in range(1, 25):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"mines_n:{i}"))
        if len(row) == 6:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад", callback_data="game:custom",
                                      style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ============================================================
#                    ПОПОЛНЕНИЕ
# ============================================================
def deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="CryptoBot",
            callback_data="dep:crypto",
            icon_custom_emoji_id="5195058841988914267",
            style="primary"
        )],
        [InlineKeyboardButton(
            text="xRocket",
            callback_data="dep:xrocket",
            icon_custom_emoji_id="5379612946747921985",
            style="primary"
        )],
        [InlineKeyboardButton(
            text="Telegram Stars",
            callback_data="dep:stars",
            icon_custom_emoji_id="5895708410447401643",
            style="primary"
        )],
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


# ============================================================
#                    ВЫВОД
# ============================================================
def withdraw_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="CryptoBot",
            callback_data="wd:crypto",
            icon_custom_emoji_id="5195058841988914267",
            style="primary"
        )],
        [InlineKeyboardButton(
            text="xRocket",
            callback_data="wd:xrocket",
            icon_custom_emoji_id="5379612946747921985",
            style="primary"
        )],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])


# ============================================================
#                    РЕФЕРАЛЫ / BACK
# ============================================================
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


# ============================================================
#                    АЛИАСЫ
# ============================================================
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