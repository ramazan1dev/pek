import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import os

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище данных пользователей
user_data = {}

# Состояния
class SalaryInput(StatesGroup):
    role = State()
    hours = State()
    rate = State()
    percent = State()
    sales = State()

# Кнопки ролей
role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Официант"), KeyboardButton(text="Повар")],
        [KeyboardButton(text="Бариста"), KeyboardButton(text="Кассир")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Меню действий после расчёта
actions_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 Посчитать ещё", callback_data="restart"),
            InlineKeyboardButton(text="➕ + еще смена", callback_data="add_more")
        ],
        [
            InlineKeyboardButton(text="🧮 Общая сумма", callback_data="show_total"),
            InlineKeyboardButton(text="🧹 Обнулить всё", callback_data="reset_all")
        ]
    ]
)

# /start
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Ассаламу алейкум! с вами Бот Рамазана\n\n"
        "Это бот для подсчета твоей (никому не нужной 😁) зарплаты за день в Пекариусе 💸\n\n"
        "👉 Выбери свою роль в Пекариусе:\nк примеру дохлый офик",
        reply_markup=role_kb
    )
    await state.set_state(SalaryInput.role)

# Роль
@dp.message(SalaryInput.role)
async def get_role(message: types.Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer("⏱ Сколько часов ты сегодня отработал?🧐", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SalaryInput.hours)

# Часы
@dp.message(SalaryInput.hours)
async def get_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        await state.update_data(hours=hours)
        await message.answer("💵 Какая у тебя ставка в час?")
        await state.set_state(SalaryInput.rate)
    except ValueError:
        await message.answer("❌ Введи число, например: 8")

# Ставка
@dp.message(SalaryInput.rate)
async def get_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        await state.update_data(rate=rate)
        await message.answer("📈 Какой у тебя процент от кассы?\nЕсли нет — введи 0.")
        await state.set_state(SalaryInput.percent)
    except ValueError:
        await message.answer("❌ Введи число, например: 300")

# Процент
@dp.message(SalaryInput.percent)
async def get_percent(message: types.Message, state: FSMContext):
    try:
        percent = float(message.text)
        await state.update_data(percent=percent)
        await message.answer("💰 На какую сумму ты сегодня продал? (касса твоя)\nЕсли нет — введи 0.")
        await state.set_state(SalaryInput.sales)
    except ValueError:
        await message.answer("❌ Введи число, например: 5000")

# Продажи
@dp.message(SalaryInput.sales)
async def get_sales(message: types.Message, state: FSMContext):
    try:
        sales = float(message.text)
        data = await state.get_data()
        role = data["role"]
        hours = data["hours"]
        rate = data["rate"]
        percent = data["percent"]

        base_pay = hours * rate
        bonus = (percent / 100) * sales
        total = base_pay + bonus
        date = datetime.now().strftime("%d.%m.%Y")
        user_id = message.from_user.id

        if user_id not in user_data:
            user_data[user_id] = {"history": []}
        user_data[user_id]["history"].append(total)

        await message.answer(
            f"📊 *Твоя пакъирская зарплата за {date}:*\n\n"
            f"🧑‍💼 *Должность:* `{role}`\n"
            f"⏱ *Часы:* `{hours}` ч.\n"
            f"💵 *Ставка:* `{rate}₽`\n"
            f"📈 *Процент:* `{percent}%`\n"
            f"💰 *Касса:* `{sales}₽`\n"
            f"───────────────\n"
            f"🔹 *Итого:* `{total:.2f}₽`",
            parse_mode="Markdown",
            reply_markup=actions_kb
        )

        await state.clear()

    except ValueError:
        await message.answer("❌ Введи число, например: 5000")

# Кнопка "Посчитать ещё"
@dp.callback_query(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🔄 Посчитаем заново!\n\n👉 Выбери свою должность:", reply_markup=role_kb)
    await state.set_state(SalaryInput.role)
    await callback.answer()

# ➕ Добавить ещё ЗП
@dp.callback_query(lambda c: c.data == "add_more")
async def add_more(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("➕ Добавим ещё одну ЗП!\n\n👉 Выбери свою должность:", reply_markup=role_kb)
    await state.set_state(SalaryInput.role)
    await callback.answer()

# 🧮 Общая сумма
@dp.callback_query(lambda c: c.data == "show_total")
async def show_total(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_data and user_data[user_id]["history"]:
        all_salaries = user_data[user_id]["history"]
        total = sum(all_salaries)
        await callback.message.answer(
            f"💰 Общая сумма всех добавленных ЗП: `{total:.2f}₽`\nЗаписей: {len(all_salaries)}",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer("🤷‍♂️ Пока что нет сохранённых ЗП.")
    await callback.answer()

# 🧹 Обнулить всё
@dp.callback_query(lambda c: c.data == "reset_all")
async def reset_all(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data[user_id] = {"history": []}
    await callback.message.answer("🧹 Вся история зарплат удалена!")
    await callback.answer()

# Команда /итог
@dp.message(Command("итог"))
async def total_salary(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]["history"]:
        all_salaries = user_data[user_id]["history"]
        total = sum(all_salaries)
        await message.answer(
            f"💰 Общая сумма зарплаты: `{total:.2f}₽`\n\nЗаписей: {len(all_salaries)}",
            parse_mode="Markdown"
        )
    else:
        await message.answer("🤷‍♂️ У тебя пока нет сохранённых зарплат.")

# Команда /сброс
@dp.message(Command("сброс"))
async def reset_salary(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"history": []}
    await message.answer("🗑️ Все сохранённые зарплаты сброшены!")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
