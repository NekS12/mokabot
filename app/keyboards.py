from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

# Клавиатура
# main клавитура, начинает со старта
main = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton('Сделать Заказ'),
    KeyboardButton('Оставить отзыв'),
]
main.add(*buttons)

main_admin = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton('Сделать Заказ'),
    KeyboardButton('Оставить отзыв'),
    KeyboardButton('Админ-Панель')
]
main_admin.add(*buttons)

main_admin_setting = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton('Добавить Товар'),
    KeyboardButton('Удалить Товар'),
    KeyboardButton('Добавить в Стоп-лист'),
    KeyboardButton("Убрать из Стоп-листа"),
    KeyboardButton('Стоп-лист'),
    KeyboardButton('Назад на Главную')
]
main_admin_setting.add(*buttons)

main_admin_setting_all_category = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Giro"),
    KeyboardButton("Супы"),
    KeyboardButton("Пасты"),
    KeyboardButton("Завтраки"),
    KeyboardButton("Салаты"),
    KeyboardButton("Десерты"),
    KeyboardButton("Классическое Кофе"),
    KeyboardButton("Холодный Кофе"),
    KeyboardButton("Рафы"),
    KeyboardButton("Чаи"),
    KeyboardButton("Лимонады"),
    KeyboardButton("Смузи & Милкшейки"), #удалена корзина
    KeyboardButton("Сиропы"),
    KeyboardButton("Назад в Админ-Панель")
]
main_admin_setting_all_category.add(*buttons)

order_kb = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Кухня"),
    KeyboardButton("Giro"),
    KeyboardButton("Напитки"),
    KeyboardButton("Корзина"),
    KeyboardButton("Назад на Главную")
]
order_kb.add(*buttons)

kitchen = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Супы"),
    KeyboardButton("Пасты"),
    KeyboardButton("Завтраки"),
    KeyboardButton("Салаты"),
    KeyboardButton("Десерты"),
    KeyboardButton("Корзина"),
    KeyboardButton("Назад в меню"),
]
kitchen.add(*buttons)

drink = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Классическое Кофе"),
    KeyboardButton("Холодный Кофе"),
    KeyboardButton("Рафы"),
    KeyboardButton("Чаи"),
    KeyboardButton("Лимонады"),
    KeyboardButton("Смузи & Милкшейки"),
    KeyboardButton("Сиропы"),
    KeyboardButton("Корзина"),
    KeyboardButton("Назад в меню")

]
drink.add(*buttons)


main_admin_setting_add_to_stoplist = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Giros"),
    KeyboardButton("Супы"),
    KeyboardButton("Пасты"),
    KeyboardButton("Завтраки"),
    KeyboardButton("Салаты"),
    KeyboardButton("Десерты"),
    KeyboardButton("Классическое Кофе"),
    KeyboardButton("Холодный Кофе"),
    KeyboardButton("Рафы"),
    KeyboardButton("Чаи"),
    KeyboardButton("Лимонады"),
    KeyboardButton("Смузи & Милкшейки"),
    KeyboardButton("Сиропы"),
    KeyboardButton("Назад")
]
main_admin_setting_add_to_stoplist.add(*buttons)

cart = ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    KeyboardButton("Оформить заказ"),
    KeyboardButton("Очистить корзину")
]
cart.add(*buttons)
