from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_admin: bool = False):
    rows = [
        [
            KeyboardButton(text="Кошелёк",
                           icon_custom_emoji_id="5310262449121827356",
                           style="primary"),
            KeyboardButton(text="Играть",
                           icon_custom_emoji_id="5309815458990433715",
                           style="success"),
            KeyboardButton(text="Меню",
                           icon_custom_emoji_id="5228868704283962338",
                           style="primary"),
        ],
    ]
    if is_admin:
        rows.append([
            KeyboardButton(text="Админка",
                           icon_custom_emoji_id="5463289097336405244",
                           style="danger")
        ])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True
    )