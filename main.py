import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime

API_TOKEN = '7283669108:AAHPESJSQivUrxx_Wtnkh9rtLvYJxAzR2Hg'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DATABASE = 'bot_db.sqlite'


async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY,
                            age INTEGER,
                            plan TEXT,
                            notification_time TEXT)''')
        await db.commit()


async def insert_user(user_id, age, plan, notification_time):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('INSERT OR REPLACE INTO users (user_id, age, plan, notification_time) VALUES (?, ?, ?, ?)',
                         (user_id, age, plan, notification_time))
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT age, plan, notification_time FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()


def create_daily_plan(age):
    if age < 16:
        return ("Ваш план на сегодня:\n"
                "1. Пробежка - 30 минут\n"
                "2. Завтрак - 20 минут\n"
                "3. Учеба - 2 часа\n"
                "4. Игры - 1 час\n"
                "5. Чтение книги - 1 час\n"
                "6. Ужин - 30 минут")
    elif age < 18:
        return ("Ваш план на сегодня:\n"
                "1. Утренняя зарядка - 20 минут\n"
                "2. Завтрак - 30 минут\n"
                "3. Учеба - 3 часа\n"
                "4. Хобби - 2 часа\n"
                "5. Время с друзьями - 2 часа\n"
                "6. Ужин - 30 минут")
    else:
        return ("Ваш план на сегодня:\n"
                "1. Утреннее упражнение - 30 минут\n"
                "2. Завтрак - 30 минут\n"
                "3. Рабочее время - 8 часов\n"
                "4. Спортивная тренировка - 1 час\n"
                "5. Личное время - 1 час\n"
                "6. Ужин - 1 час\n"
                "7. Отдых и чтение - 1 час")


async def send_notifications():
    while True:
        now = datetime.now().strftime("%H:%M")
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute('SELECT user_id, plan, notification_time FROM users') as cursor:
                async for row in cursor:
                    user_id, plan, notification_time = row
                    if now == notification_time:
                        try:
                            await bot.send_message(user_id, f"Напоминание: {plan}")
                        except Exception as e:
                            logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        await asyncio.sleep(60)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    logging.info(f"Received /start command from user {user_id}")
    await message.reply("Привет! Сколько вам лет?")

@dp.message_handler(lambda message: message.text.isdigit())
async def handle_age(message: types.Message):
    user_id = message.from_user.id
    age = int(message.text)
    logging.info(f"Received age {age} from user {user_id}")

    if age > 0:
        plan = create_daily_plan(age)
        notification_time = "09:00"
        await insert_user(user_id, age, plan, notification_time)
        await message.reply(f"Спасибо! Ваш план на день:\n{plan}\n\nБуду напоминать вам в {notification_time}.")
    else:
        await message.reply("Пожалуйста, введите корректный возраст.")



@dp.message_handler(lambda message: not message.text.isdigit())
async def handle_invalid_input(message: types.Message):
    await message.reply("Пожалуйста, введите ваш возраст числом.")


async def on_startup(dp):
    await init_db()
    # Исправьте вызов фоновой задачи
    asyncio.create_task(send_notifications())



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
