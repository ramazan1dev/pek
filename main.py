import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# 🔐 ВСТАВЬ СВОЙ ТОКЕН СЮДА
API_TOKEN = "7083246117:AAHlFXXsswI-gOB5DleP5GomDwJ4VBPswPM"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

# /start
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Ассаламу алейкум!\n\n"
        "Это бот для подсчета твой (никому не нужной😁)зарплаты за день в Пекариусе 💸\n"
        "в дальнейшем он должен быть крутым,ну а пока что ленивый Рамазан создал только это 'чудо'"
        "👉 Выбери свою роль в Пекариусе:"
        "К примеру Дохлый офик,там внизу кнопка есть",
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
        await message.answer("💵 Какая у тебя ставка в час? Ну процент да")
        await state.set_state(SalaryInput.rate)
    except ValueError:
        await message.answer("❌ Введи да число говорю же, пример: 8")

# Ставка
@dp.message(SalaryInput.rate)
async def get_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        await state.update_data(rate=rate)
        await message.answer("📈 Сколько процентов с продаж ты получаешь?😉\nЕсли нет — введи 0.")
        await state.set_state(SalaryInput.percent)
    except ValueError:
        await message.answer("❌ Введи число мал, пример: 300")

# Процент
@dp.message(SalaryInput.percent)
async def get_percent(message: types.Message, state: FSMContext):
    try:
        percent = float(message.text)
        await state.update_data(percent=percent)
        await message.answer("💰 На какую сумму ты сегодня продал? (касса твоя)\nЕсли нет — введи 0.")
        await state.set_state(SalaryInput.sales)
    except ValueError:
        await message.answer("❌ Введи число ваяяя, пример: 5000 ну типо слитно короче")

# Продажи
@dp.message(SalaryInput.sales)
async def get_sales(message: types.Message, state: FSMContext):
    try:
        sales = float(message.text)
        user_data = await state.get_data()
        role = user_data["role"]
        hours = user_data["hours"]
        rate = user_data["rate"]
        percent = user_data["percent"]

        base_pay = hours * rate
        bonus = (percent / 100) * sales
        total = base_pay + bonus
        date = datetime.now().strftime("%d.%m.%Y")

        restart_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Посчитать ещё", callback_data="restart")]
            ]
        )

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
            reply_markup=restart_kb
        )

        await state.clear()

    except ValueError:
        await message.answer("❌ Введи число нормально, пример: 5000")

# Начать заново
@dp.callback_query(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🔄 Посчитаем заново!\n\n👉 Выбери свою бедную должность:", reply_markup=role_kb)
    await state.set_state(SalaryInput.role)
    await callback.answer()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
