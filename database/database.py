import asyncio
import aiomysql


async def write_in_db(user_id, article_id, product_name, price, price_card):
    conn = await aiomysql.connect(
        host='localhost',
        port=3306,
        user='user',
        password='password',
        db='bd'
    )

    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM test_table WHERE articule = %s AND user_id = %s",
            (article_id, user_id)
        )
        exists = await cur.fetchone()

        if exists[0] > 0:
            await cur.execute(
                "UPDATE test_table SET product_name = %s, price = %s, price_card = %s WHERE articule = %s AND user_id = %s",
                (product_name, price, price_card, article_id, user_id)
            )
        else:
            await cur.execute(
                "INSERT INTO test_table (user_id, articule, product_name, price, price_card) VALUES (%s, %s, %s, %s, %s)",
                (user_id, article_id, product_name, price, price_card)
            )

        await conn.commit()
    conn.close()


async def show_all():
    conn = await aiomysql.connect(host='localhost', port=3306, user='user', password='password', db='bd')

    async with conn.cursor() as cur:
        await cur.execute("SELECT * from test_table;")
        result = await cur.fetchall()
        for row in result:
            print(row)
    conn.close()


async def show_saved(user_id):
    conn = await aiomysql.connect(host='localhost', port=3306, user='user', password='password', db='bd')

    async with conn.cursor() as cur:
        await cur.execute("SELECT * FROM test_table WHERE user_id = %s;", (user_id,))
        result = await cur.fetchall()
    conn.close()
    return result


async def delete_article(articule, user_id):
    conn = await aiomysql.connect(host='localhost', port=3306, user='user', password='password', db='bd')
    async with conn.cursor() as cur:
        delete_query = "DELETE FROM test_table WHERE articule = %s AND user_id = %s;"
        await cur.execute(delete_query, (articule, user_id))
        await conn.commit()
        print(f"Артикул '{articule}' для пользователя '{user_id}' успешно удалён.")
    conn.close()


def console_input_loop():
    while True:
        inp = input()
        if inp == "/close":
            print("Закрытие бота...")
            break
        elif inp == "/show":
            asyncio.run(show_all())
        elif inp.split()[0] == "/delete":
            try:
                articule = int(inp.split()[1])
                user_id = int(inp.split()[2])
                asyncio.run(delete_article(articule, user_id))
            except IndexError:
                print("Не введён артикул или ID пользователя.")
            except ValueError:
                print("Артикул и ID пользователя должны быть целыми числами.")
        elif inp == "/help":
            print("/close - это закрыть базу данных\n"
                  "/show - Показать таблицу\n")
        else:
            print("Команда не найдена")
