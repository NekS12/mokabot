import sqlite3 as sq

db = sq.connect("products.db")
cur = db.cursor()

async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts_order("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "tg_id INTEGER, "
                "cart_id TEXT) ")

    cur.execute("CREATE TABLE IF NOT EXISTS products("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT, "
                "desc TEXT, "
                "price Text, "
                "photo TEXT, "
                "brand TEXT,"
                "available BOOLEAN) ")

    cur.execute("CREATE TABLE IF NOT EXISTS list_category("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT) ")


    db.commit()
# карточка товара
orders={}# заказ товара(корзина) - словарь
