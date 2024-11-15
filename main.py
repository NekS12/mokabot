import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.types import Message
from app import keyboards as kb
from dotenv import load_dotenv
from app import database as db
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import uuid
import os
import sqlite3
import datetime
from yookassa import Payment, Configuration
import yookassa

"""ОБРАБОТКА ВРЕМЕНИ"""
def is_allowed_hours():
    current_time = datetime.datetime.now()
    start_time = datetime.time(9, 0)  # 10:00
    end_time = datetime.time(22, 0)   # 18:00

    return start_time <= current_time.time() < end_time


async def check_allowed_hours(func):
    async def wrapper(message: Message):
        if is_allowed_hours():
            await func(message)
        else:
            await message.answer("Боту разрешено работать только с 09:00 до 21:00.")

    return wrapper

def get_available_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, price, photo 
        FROM products
        WHERE available = 1
    ''')

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"id": p[0], "name": p[1], "price": p[2], "photo": p[3]} for p in products]


load_dotenv()
storage = MemoryStorage()
token = os.getenv("TOKEN")

bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)
orders={}

class Form(StatesGroup):
    question_one = State()
    question_two = State()
    question_three = State()
    payment_state = State()

class StopListStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waitingg_for_name= State()
# Определяем состояния для добавления товара
class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_delete_name = State()

class PaymentsInfoStates(StatesGroup):
    waiting_for_time_visit = State()
    waiting_for_place_order = State()
    waitingg_for_comment = State()
    waiting_for_finalization = State()

    @classmethod
    def get_current_state(cls):
        return cls.__dict__['_states'][cls._current_state]

    @classmethod
    def set_current_state(cls, state):
        cls._current_state = state


async def on_startup(_):
    await db.db_start()
    print("Start Bot")


#Запрос к БД на получение всех товаров
def get_all_products():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('SELECT name, id FROM products')
    products = cursor.fetchall()

    if products:
        return [{"name": p[0], "id": p[1]} for p in products]
    else:
        return []

#Создание клавиатуры для выбора товара
def create_product_keyboard(products):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        button = InlineKeyboardButton(product["name"], callback_data=f"product:{product['id']}")
        keyboard.insert(button)
    return keyboard


@check_allowed_hours
@dp.message_handler(commands=['start'])
async def get_start(message: Message):
    if is_allowed_hours():
        message_texth = (
            f"Привет {message.from_user.first_name}\n"
        )
        #await message.answer(f"Привет {message.from_user.first_name}")
        await message.answer(f"Для управления нажми на кнопки внизу", reply_markup=kb.main)
        await message.answer_photo(photo="AgACAgIAAxkBAAIL02bZpQ5yFoYAAREu4JFvi4j_7DeMRAACrOAxG17F0Eo9YfcPy3fvewEAAwIAA3kAAzYE", caption=message_texth)
        if message.from_user.id == int(os.getenv("ADMIN_ID")):
            await message.answer("ПАНЕЛЬ АДМИНИСТРАТОРА ВКЛЮЧЕНА", reply_markup=kb.main_admin)
    else:
        await message.answer("Боту разрешено работать только с 08:00 до 23:00.")

@dp.message_handler(commands=["id"]) # УДАЛИТЬ (Проверка id пользователя)
async def cmd_id(message: Message):
    await message.answer(f"{message.from_user.id}")

@dp.message_handler(content_types=['photo']) # УДАЛИТЬ (Проверка id фото)
async def cmd_id(message: Message):
    photo_id = message.photo[-1].file_id  # Используем наибольшее качество фото
    await message.answer(f"ID вашего фото: {photo_id}")


@dp.message_handler(text="Оставить отзыв")
async def feedback(message: Message):
    gis = 'https://go.2gis.com/jklwi'
    yandex='https://yandex.ru/maps/-/CDheiVm-'
    keyboard = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton("Яндекс", url=yandex)
    cancel_button = InlineKeyboardButton("2ГИС", url= gis)
    keyboard.add(pay_button, cancel_button)
    if is_allowed_hours():
        await message.answer(f"Оставить отзыв можно тут: ", reply_markup=keyboard)

@dp.message_handler(text="Сделать Заказ") # Обработчик "Сделать Заказ"
async def order(message: Message):
    if is_allowed_hours():
        await message.answer(f"Выберите Кухню или нажмите 'Назад'", reply_markup=kb.order_kb)
    else:
        await message.answer("Заказы принимаются только с 09:00 до 21:00.")


@dp.message_handler(text="Админ-Панель") # Обработчик "Админ-Панель"
async def order(message: Message):
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer(f"Выберите Категория или нажмите 'Назад'", reply_markup=kb.main_admin_setting)


@dp.message_handler(text="Добавить Товар") # Команда для начала добавления товара
async def cmd_add_product(message: types.Message):
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Выберите категорию товара", reply_markup=kb.main_admin_setting_all_category)
        await AddProductStates.waiting_for_category.set()

@dp.message_handler(state=AddProductStates.waiting_for_category)
async def process_category(message: types.Message, state: FSMContext):
    category_name = message.text

    # Проверка существования категории
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM list_category WHERE name = ?', (category_name,))
    category = cursor.fetchone()

    if category:
        await state.update_data(category_id=category[0])
        await message.answer("Введите название товара:")
        await AddProductStates.waiting_for_name.set()
    elif message.text == "Назад в Админ-Панель" and message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Вы вернулись назад", reply_markup=kb.main_admin)
        await state.finish()
        await state.finish() # Завершаем текущее состояние
    else:
        await message.answer("Категория не найдена. Попробуйте снова:")
        return

@dp.message_handler(state=AddProductStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await AddProductStates.waiting_for_description.set()

@dp.message_handler(state=AddProductStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара:")
    await AddProductStates.waiting_for_price.set()

@dp.message_handler(state=AddProductStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Отправьте фото товара:")
        await AddProductStates.waiting_for_photo.set()
    except ValueError:
        await message.answer("Цена должна быть числом. Попробуйте снова:")

@dp.message_handler(content_types=['photo'], state=AddProductStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Сохраняем фото и информацию о товаре в базе данных
    photo_id = message.photo[-1].file_id  # Получаем ID самого высокого качества фото
    # Получаем данные о товаре из состояния
    category_id = data.get('category_id')
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    photo_id = message.photo[-1].file_id  # Получаем ID самого высокого качества фото

    # Сохраняем информацию о товаре в базе данных
    try:
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()

        # Вставка данных о товаре в таблицу
        cursor.execute('''
                INSERT INTO products (name, desc, price, photo, brand, available)
                VALUES (?, ?, ?, ?, ?, "true")
            ''', (name, description, price, photo_id, category_id))

        conn.commit()
        await message.answer("Товар успешно добавлен!")
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении товара. Пожалуйста, попробуйте снова.")
        print(f"Error: {e}")
    finally:
        conn.close()

    # Завершение состояния после добавления товара
    await state.finish()
    await AddProductStates.waiting_for_category.set()


"""СТОП ЛИСТ"""

@dp.message_handler(text="Добавить в Стоп-лист")
async def start_add_to_stoplist(message: types.Message):
    await message.answer("Теперь введите название товара:")
    await StopListStates.waiting_for_name.set()


@dp.message_handler(state=StopListStates.waiting_for_name)
async def handle_stoplist_product_name(message: types.Message, state: FSMContext):
    product_name = message.text

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    SELECT * FROM products
    WHERE name = ?
    """
    cursor.execute(query, (product_name,))
    result = cursor.fetchone()

    conn.close()

    if result:
        product_info = f"""
        Название: {result[1]}
        Цена: {result[2]}
        Описание: {result[3]}
        """

        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("В стоп-лист", callback_data=f"stoplist_{product_name}")
        keyboard.add(button)

        await message.answer(product_info, reply_markup=keyboard)
    elif message.text == "Назад на Главную" and message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Вы вернулись назад", reply_markup=kb.main_admin)
        await state.finish()
        await state.finish()  # Завершаем текущее состояние
    else:
        await message.answer("Товар не найден в базе данных.")

    await state.finish()

@dp.callback_query_handler(lambda call: call.data.startswith("stoplist_"))
async def add_to_stoplist(call: types.CallbackQuery):
    product_name = call.data.split("_")[1]

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE products
            SET available = 'false'
            WHERE name =?
        """, (product_name,))

        affected_rows = cursor.rowcount

        if affected_rows == 0:
            raise ValueError("Товар не найден в базе данных.")

        conn.commit()
        await call.message.answer(f"Товар '{product_name}' добавлен в стоп-лист.")
    except sqlite3.Error as e:
        conn.rollback()
        await call.message.answer(f"Произошла ошибка при добавлении в стоп-лист: {str(e)}")
    finally:
        conn.close()

    await call.answer()


@dp.message_handler(text="Стоп-лист")
async def show_stoplist(message: types.Message):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    SELECT brand, name, price, desc
    FROM products
    WHERE available IS 'false'
    ORDER BY brand, name
    """
    cursor.execute(query)
    stoplist_products = cursor.fetchall()

    conn.close()

    if not stoplist_products:
        await message.answer("Стоп-лист пуст.")
        return

    stoplist_message = "Текущий стоп-лист:\n\n"

    for product in stoplist_products:
        stoplist_message += f"{product[0]} - {product[1]}\n"

    await message.answer(stoplist_message)


class StopListMenuStates(StatesGroup):
    waiting_for_choice = State()




@dp.message_handler(state=StopListMenuStates.waiting_for_choice)
async def handle_stoplist_menu(message: types.Message, state: FSMContext):
    choice = message.text

    if choice == "Показать стоп-лист":
        await show_stoplist_products(message)
    elif choice == "Удалить из стоп-листа":
        await remove_from_stoplist(message)

    await state.finish()


async def show_stoplist_products(message: types.Message):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    SELECT brand, name, price, description
    FROM products
    WHERE available IS 'false'
    ORDER BY brand, name
    """
    cursor.execute(query)
    stoplist_products = cursor.fetchall()

    conn.close()

    if not stoplist_products:
        await message.answer("Стоп-лист пуст.")
        return

    stoplist_message = "Текущий стоп-лист:\n\n"

    for product in stoplist_products:
        stoplist_message += f"{product[0]} - {product[1]}\n"

    await message.answer(stoplist_message)


async def remove_from_stoplist(message: types.Message):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    SELECT brand, name
    FROM products
    WHERE available IS 'false'
    ORDER BY brand, name
    """
    cursor.execute(query)
    stoplist_products = cursor.fetchall()

    conn.close()

    if not stoplist_products:
        await message.answer("Стоп-лист пуст.")
        return

    # Создаем инлайн-клавиатуру для выбора товаров
    inline_kb = InlineKeyboardMarkup(row_width=1)
    buttons = []
    for product in stoplist_products:
        button = InlineKeyboardButton(f"{product[0]} - {product[1]}", callback_data=f"remove_{product[1]}")
        buttons.append(button)
    inline_kb.add(*buttons)

    await message.answer("Выберите товар для удаления из стоп-листа:", reply_markup=inline_kb)


@dp.callback_query_handler(lambda call: call.data.startswith("remove_"))
async def remove_product_from_stoplist(call: types.CallbackQuery):
    product_name = call.data.split("_")[1]

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    UPDATE products
    SET available = 'true'
    WHERE name = ?
    """
    cursor.execute(query, (product_name,))
    conn.commit()

    conn.close()

    await call.message.edit_text(f"Товар '{product_name}' удален из стоп-листа.")
    await call.answer()

@dp.message_handler(text="Убрать из Стоп-листа")
async def remove_product_from_stoplist(message: types.Message):
    await message.answer("Введите название товара, который вы хотите удалить из стоп-листа:")
    await StopListStates.waitingg_for_name.set()


@dp.message_handler(state=StopListStates.waitingg_for_name)
async def process_remove_product_name(message: types.Message, state: FSMContext):
    product_name = message.text

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    SELECT id, name, desc, price, photo, brand, available
    FROM products
    WHERE name =?
    """
    cursor.execute(query, (product_name,))
    product = cursor.fetchone()

    conn.close()

    if product:
        product_info = {
            "name": product[1],
            "description": product[2],
            "price": product[3],
            "photo": product[4],
            "brand": product[5],
            "available": product[6]
        }

        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("Удалить из стоп-листа", callback_data=f"remove_{product_name}")
        keyboard.add(button)

        await message.answer(
            f"Информация о товаре:\n\n{product_info['name']}\n{product_info['description']}\nЦена: {product_info['price']}",
            reply_markup=keyboard)

        await state.finish()
    elif message.text == "Назад на Главную" and message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Вы вернулись назад", reply_markup=kb.main_admin)
        await state.finish()
        await state.finish() # Завершаем текущее состояние
    else:
        await message.answer("Товар не найден в базе данных.")


@dp.callback_query_handler(lambda call: call.data.startswith("remove_"))
async def remove_product_from_stoplist(call: types.CallbackQuery):
    product_name = call.data.split("_")[1]

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = """
    UPDATE products
    SET available = CASE WHEN available = 'false' THEN 'true' ELSE 'false' END
    WHERE name =?
    """
    cursor.execute(query, (product_name,))
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()

    if affected_rows > 0:
        await call.message.answer(f"Товар '{product_name}' успешно убран из стоп-листа.")
    else:
        await call.message.answer(f"Ошибка: товар '{product_name}' не найден в стоп-листе.")

    await call.answer()


@dp.message_handler(text="Удалить Товар")
async def delete_product(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара, который хотите удалить:")
    await AddProductStates.waiting_for_delete_name.set()




@dp.message_handler(state=AddProductStates.waiting_for_delete_name) #удаление товара
async def process_delete_name(message: types.Message, state: FSMContext):
    product_name = message.text

    # Проверка существования товара
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM products WHERE name = ?', (product_name,))
    product = cursor.fetchone()

    if product:
        # Удаляем товар из базы данных
        cursor.execute('DELETE FROM products WHERE name = ?', (product[0],))
        conn.commit()
        await message.answer("Товар успешно удален!")
    elif message.text == "Назад на Главную" and message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Вы вернулись назад", reply_markup=kb.main_admin)
        await state.finish()
        await state.finish() # Завершаем текущее состояние
    else:
        await message.answer("Товар не найден. Попробуйте снова:")

    conn.close()




stop_list_menu = InlineKeyboardMarkup()
stop_list_menu.add(InlineKeyboardButton("Показать товары", callback_data="stop_list_show"))
stop_list_menu.add(InlineKeyboardButton("Изменить доступность", callback_data="stop_list_change"))
stop_list_menu.add(InlineKeyboardButton("Назад", callback_data="stop_list_back"))

@dp.message_handler(text="Стоп-Лист")
async def show_stop_list(message: types.Message):
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer("Выберите действие:", reply_markup= stop_list_menu)


@dp.callback_query_handler(lambda call: call.data.startswith("stop_list_"))
async def handle_stop_list(call: types.CallbackQuery):
    action = call.data.split("_")[2]
    if action == "show":
        await show_stop_list_items(call)
    elif action == "change":
        await change_availability(call)
    elif action == "back":
        await call.message.edit_text("Вы вернулись в админ-панель", reply_markup=kb.main_admin)


async def show_stop_list_items(call: types.CallbackQuery):
    products = get_all_products()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        button = InlineKeyboardButton(product["name"], callback_data=f"product:{product['id']}")
        keyboard.insert(button)

    await call.message.edit_text("Выберите товар для изменения доступности:", reply_markup=keyboard)


async def change_availability(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    # Получаем текущее значение available
    cursor.execute('SELECT available FROM products WHERE id = ?', (product_id,))
    current_available = cursor.fetchone()[0]

    # Меняем значение на противоположное
    new_available = 1 if current_available == 0 else 0
    cursor.execute('UPDATE products SET available = ? WHERE id = ?', (new_available, product_id))
    conn.commit()
    conn.close()

    await call.answer(f"Доступность товара изменена на {'доступен' if new_available == 1 else 'недоступен'}")





#Вывод информации о товаре
@dp.callback_query_handler(lambda call: True)
async def handle_callback(call: types.CallbackQuery):
    print(f"Получено событие: {call.data}")

    if call.data.startswith("product:"):
        # Обработка нажатия на изображение блюда
        product_id = int(call.data.split(":")[1])
        product_info = get_product_info(product_id)

        if product_info:
            # Формируем сообщение с информацией
            message_text = (
                f"Имя: {product_info['name']}\n"
                f"Описание: {product_info['description']}\n"
                f"Цена: {product_info['price']}\n"
            )

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart:{product_id}"))

            # Отправляем фото, кнопки и текст вместе
            await call.message.answer_photo(photo=product_info['photo'], caption=message_text, reply_markup=keyboard)

            #await call.message.edit_reply_markup(reply_markup=keyboard)
        else:
            await call.message.edit_text("Извините, продукт не найден.", parse_mode='Markdown')

    elif call.data.startswith("add_to_cart:"):
        # Обработка нажатия на кнопку "Добавить в корзину"
        product_id = int(call.data.split(":")[1])
        product_info = get_product_info(product_id)

        if product_info:
            user_id = call.from_user.id
            if user_id not in orders:
                orders[user_id] = {}

            if product_id in orders[user_id]:
                orders[user_id][product_id]["count"] += 1
            else:
                orders[user_id][product_id] = {"name": product_info["name"], "price": product_info["price"], "count": 1}

            await call.message.answer(
                f"Товар {product_info['name']} успешно добавлен в корзину. Количество: {orders[user_id][product_id]['count']}")
        else:
            await call.message.answer("Извините, продукт не найден.")




def get_product_info(product_id):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT name, desc, price, photo, brand, available = true 
        FROM products
        WHERE id =?
    ''', (product_id,))
#888888
    product = cursor.fetchone()

    if product:
        return {
            "name": product[0],
            "description": product[1],
            "price": float(product[2]),  # Убедимся, что цена - это число
            "photo": product[3],
            "brand": product[4]
        }
    else:
        return None

@dp.message_handler(text="Кухня") # Обработчик "Кухня"
async def order(message: Message):
    await message.answer(f"Выберите Категорию или нажмите 'Назад'", reply_markup=kb.kitchen)

@dp.message_handler(text=["Супы", "Пасты", "Завтраки", "Салаты", "Десерты"])
async def kitchen_menu(message: Message):
    category = message.text
    products = get_products_by_category(category)
    if not products:
        await message.answer("К сожалению, в этой категории нет доступных товаров.")
        return
    else:
        keyboard = create_product_keyboard(products)
        await message.answer("Выберите блюдо:", reply_markup=keyboard)


def get_products_by_category(category):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    query = "SELECT id, name FROM products WHERE brand = ? AND available = 'true'"
    cursor.execute(query, (category,))

    # Получаем все результаты
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    # Преобразуем кортежи в словари для удобства
    return [{"id": product[0], "name": product[1]} for product in products]


@dp.message_handler(text="Напитки") # Обработчик "Напитки"
async def order(message: Message):
    await message.answer(f"Выберите Категорию или нажмите 'Назад'", reply_markup=kb.drink)

@dp.message_handler(text=["Классическое Кофе", "Холодный Кофе", "Холодный Кофе", "Чаи", "Лимонады", "Смузи & Милкшейки", "Рафы", "Сиропы"])
async def drink_menu(message: Message):
    category = message.text  # Получаем категорию из текста сообщения
    products = get_products_by_category(category)  # Получаем товары по категории
    if not products:
        await message.answer("К сожалению, в этой категории нет доступных товаров.")
        return
    else:
        keyboard = create_product_keyboard(products)
        await message.answer("Выберите блюдо:", reply_markup=keyboard)
#@dp.message_handler(text="Giro") # Обработчик "Giro"
#async def order(message: Message):
#    await message.answer(f"Выберите товар или нажмите 'Назад'", reply_markup=kb.giro)

@dp.message_handler(text=["Giro"])
async def giro_menu(message: Message):
    category = message.text  # Получаем категорию из текста сообщения
    products = get_products_by_category(category)  # Получаем товары по категории
    if not products:
        await message.answer("К сожалению, в этой категории нет доступных товаров.")
        return
    else:
        keyboard = create_product_keyboard(products)
        await message.answer("Выберите блюдо:", reply_markup=keyboard)


order_number_generator = iter(range(1000000))


@check_allowed_hours
@dp.message_handler(text="Оформить заказ")
async def place_order(message: types.Message):
    await Form.question_one.set()
    await message.answer("Выберите: С собой или здесь?")



@dp.message_handler(state=Form.question_one)
async def process_question_one(message: types.Message, state: FSMContext):
    await state.update_data(answer_one=message.text)
    await Form.question_two.set()
    await message.answer("К какому времени вы будете? Например: 14:00")

@dp.message_handler(state=Form.question_two)
async def process_question_two(message: types.Message, state: FSMContext):
    await state.update_data(answer_two=message.text)
    await Form.question_three.set()
    await message.answer("Комментарий к заказу. Если его нет, отправте '-'")

@dp.message_handler(state=Form.question_three)
async def process_question_three(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in orders:
        await message.answer("Ваша корзина пуста. Выберите товары для покупки.")
        return

    cart_items = orders[user_id]

    # Генерируем номер заказа
    current_order_number = next(order_number_generator)
    new_order = {
        "number": current_order_number,
        "user_id": user_id,
        "items": []
    }
    orders[current_order_number] = new_order

    # Создаем сообщение с информацией о заказе
    order_message = f"Заказ №{current_order_number}:\n\n"
    for product_id, item in cart_items.items():
        product_info = get_product_info(product_id)
        if product_info:
            order_message += f"- {product_info['name']} x{item['count']} = {product_info['price'] * item['count']}\n"
        else:
            order_message += f"- Товар не найден\n"
    await state.update_data(answer_three=message.text)
    user_data = await state.get_data()
    order_message +=(f"\nКомментарии к заказу:\n"
                        f"-Где будете кушать: {user_data['answer_one']}\n"
                        f"-Время подачи: {user_data['answer_two']}\n"
                        f"-Комментарий: {user_data['answer_three']}" 
                        f"\nОбщая сумма: {sum(item['price'] * item['count'] for item in cart_items.values())}")
    amount = sum(item['price'] * item['count'] for item in cart_items.values())
    confirmation_url, payment_id = await create(amount, message.chat.id, current_order_number)
    await state.update_data(payment_id=payment_id)
    await Form.payment_state.set()

    # конец работы state machine
    # Отправляем сообщение пользователю с информацией о заказе и инлайн-клавиатурой
    keyboard = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton("Оплатить", url= confirmation_url)
    cancel_button = InlineKeyboardButton("Отмена", callback_data="back")
    check_status_button = InlineKeyboardButton("Проверить статус платежа", callback_data="check_payment_status")
    keyboard.add(pay_button, cancel_button)
    keyboard.add(check_status_button)
    if is_allowed_hours():
        await message.answer(order_message, reply_markup=keyboard)
    else:
        await message.answer("Мы работаем с 9:00 до 21:00")


'''ОПЛАТА!!!!!!!!!'''




async def create(amount, chat_id, current_order_number):
    Configuration.account_id='472705'
    Configuration.secret_key='test_OkhBb03l4WrPp_qo1dpFVXfCz1yfkVmySy2_SCLefQQ'
    id_key = str(uuid.uuid4())
    payment= Payment.create({"amount": {
        "value": str(amount),
        "currency": "RUB"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me/Moqatest01bot"
    },
    "capture": True,
    "description": f"Оплата заказа №{current_order_number}",
    "metadata":{
        "chat_id": chat_id
    }

    }, id_key)
    payment_id=payment.id
    confirmation_url= payment.confirmation.confirmation_url
    return payment.confirmation.confirmation_url, payment.id


@dp.callback_query_handler(text="check_payment_status", state=Form.payment_state)
async def check_payment_status(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    payment_id = user_data.get('payment_id')
    user_id = callback_query.from_user.id  # Получаем ID пользователя
    GROUP_CHAT_ID= -1002172599107

    if payment_id:
        payment_status = await get_payment_status(payment_id)
        if payment_status == 'succeeded':
            await bot.send_message(callback_query.from_user.id, "Ваш платеж прошел успешно! Беремся за готовку.", reply_markup=kb.order_kb)
            cart_items = orders.get(user_id, {})
            order_message = "Состав заказа:\n"
            for product_id, item in cart_items.items():
                order_message += f"- {item['name']} x{item['count']} = {item['price'] * item['count']}\n"
                order_message += (f"\nКомментарии к заказу:\n"
                                  f"- Где будете кушать: {user_data['answer_one']}\n"
                                  f"- Время подачи: {user_data['answer_two']}\n"
                                  f"- Комментарий: {user_data['answer_three']}\n"
                                  f"Общая сумма: {sum(item['price'] * item['count'] for item in cart_items.values())}")
            await bot.send_message(GROUP_CHAT_ID,
                                   f"Новый заказ от {callback_query.from_user.username}:\n\n{order_message}")
            await state.finish()
            if user_id in orders:
                del orders[user_id]
        elif payment_status == 'pending':
            await bot.send_message(callback_query.from_user.id, "Ваш платеж в процессе обработки. Пожалуйста, подождите.")
        else:
            await bot.send_message(callback_query.from_user.id, "К сожалению, ваш платеж не прошел. Пожалуйста, попробуйте снова.")
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти информацию о платеже.")


async def get_payment_status(payment_id):
    try:
        payment = Payment.find_one(payment_id)  # Получаем платеж по его ID
        return payment.status  # Вернуть статус платежа
    except Exception as e:
        print(f"Ошибка получения статуса платежа: {e}")
        return None

@dp.callback_query_handler(text="back", state=Form.payment_state)
async def go_to_cart_from_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await show_cart(callback_query.message)  # Вызываем функцию показа корзины
    await state.finish()


'''КОРЗИНА!!!!!'''

@dp.message_handler(text="Корзина")
async def show_cart(message: Message):
    user_id = message.from_user.id

    if user_id in orders:
        cart_items = orders.get(user_id, {})

        total_sum = sum(item["price"] * item["count"] for item in cart_items.values())

        cart_message = "Ваша корзина:\n\n"
        for product_id, item in cart_items.items():
            cart_message += f"{item['name']} x{item['count']} = {item['price'] * item['count']}\n"

        cart_message += f"\nОбщая сумма: {total_sum}"

        # Создаем клавиатуру с кнопками управления
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            KeyboardButton("Оформить заказ"),
            KeyboardButton("Очистить корзину"),
            KeyboardButton("Назад в меню")
        ]
        keyboard.add(*buttons)

        await message.answer(cart_message, reply_markup=keyboard)
    else:
        await message.answer("Ваша корзина пуста.", reply_markup=kb.order_kb)


@dp.message_handler(text="Очистить корзину")
async def clear_cart(message: Message):
    user_id = message.from_user.id

    # Очищаем корзину пользователя
    orders[user_id] = {}

    # Отправляем сообщение о том, что корзина очищена
    await message.answer("Корзина успешно очищена.")

async def go_back_to_previous_state(call: types.CallbackQuery, state: FSMContext):
    async with asyncio.contextmanager() as cm:
        state = dp.current_state(user=call.from_user.id)
        state = dp.current_state(user=call.from_user.id)
        if state:
            await state.set()
            await call.message.answer("Вы вернулись к предыдущему меню", parse_mode='Markdown')
        else:
            await call.message.answer("Вы находитесь на главном меню", parse_mode='Markdown')


@dp.message_handler(text="Назад в меню") # Обработчик "Назад в меню"
async def order(message: Message):
    if is_allowed_hours():
        await message.answer(f"Выберите Кухню или нажмите 'Назад'", reply_markup=kb.order_kb)
    else:
        await message.answer("Заказы принимаются только с 09:00 до 21:00.")

@dp.message_handler(text="Назад на Главную") # Обработчик "Назад на Главную"
async def order(message: Message):
    if is_allowed_hours():
        message_texth = (
            f"Привет {message.from_user.first_name}\n"
        )
        # await message.answer(f"Привет {message.from_user.first_name}")
        await message.answer(f"Для управления нажми на кнопки внизу", reply_markup=kb.main)
        await message.answer_photo(
            photo="AgACAgIAAxkBAAIL02bZpQ5yFoYAAREu4JFvi4j_7DeMRAACrOAxG17F0Eo9YfcPy3fvewEAAwIAA3kAAzYE",
            caption=message_texth)
        if message.from_user.id == int(os.getenv("ADMIN_ID")):
            await message.answer("ПАНЕЛЬ АДМИНИСТРАТОРА ВКЛЮЧЕНА", reply_markup=kb.main_admin)
    else:
        await message.answer("Боту разрешено работать только с 08:00 до 23:00.")

@dp.message_handler(text="Назад в Админ-Панель") # Обработчик "Назад в Админ-Панель"
async def order(message: Message):
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer(f"Выберите Категория или нажмите 'Назад'", reply_markup=kb.main_admin_setting)



if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    print("Stop Bot")




