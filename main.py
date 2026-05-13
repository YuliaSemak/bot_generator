import asyncio
import os

from dotenv import load_dotenv
from openai import OpenAI

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.chat_action import ChatActionSender

# ================= LOAD ENV =================
load_dotenv()

# ================= TOKENS =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ================= CHECK TOKENS =================
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не знайдено у .env")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY не знайдено у .env")

# ================= OPENROUTER =================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# ================= BOT =================
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ================= FSM =================
class Form(StatesGroup):
    target = State()
    reason = State()
    style = State()

# ================= KEYBOARD =================
def make_kb(buttons):
    keyboard = [[KeyboardButton(text=btn)] for btn in buttons]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

# ================= START =================
@dp.message(Command("start"))
@dp.message(lambda m: m.text == "🔄 Створити ще")
async def start(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "👋 Вітаю!\n\n"
        "Кому ви хочете написати?\n"
        "Або впишіть свій варіант ✍️",
        reply_markup=make_kb([
            "Викладачу 👨‍🏫",
            "Роботодавцю 💼",
            "Другу 😎",
            "Інше ✍️"
        ])
    )

    await state.set_state(Form.target)

# ================= TARGET =================
@dp.message(Form.target)
async def target_step(message: Message, state: FSMContext):

    if len(message.text) > 100:
        await message.answer("❌ Занадто довгий текст")
        return

    await state.update_data(target=message.text)

    await message.answer(
        "📌 Яка причина повідомлення?\n"
        "Оберіть або напишіть свою ✍️",
        reply_markup=make_kb([
            "Запізнення 🕒",
            "Хвороба 🤒",
            "Не встигаю в дедлайн ⏳",
            "Потрібна консультація 📝",
            "Погане самопочуття 😵",
            "Інше ✍️"
        ])
    )

    await state.set_state(Form.reason)

# ================= REASON =================
@dp.message(Form.reason)
async def reason_step(message: Message, state: FSMContext):

    if len(message.text) > 300:
        await message.answer("❌ Занадто довгий опис")
        return

    await state.update_data(reason=message.text)

    await message.answer(
        "🎭 Оберіть стиль повідомлення\n"
        "Або напишіть свій ✍️",
        reply_markup=make_kb([
            "Офіційно-діловий 👔",
            "Дружній 😊",
            "Саркастичний 🤨",
            "Виправдальний 🙏",
            "Зухвалий 🔥",
            "Дуже короткий ⚡️"
        ])
    )

    await state.set_state(Form.style)

# ================= GENERATE =================
@dp.message(Form.style)
async def generate(message: Message, state: FSMContext):

    data = await state.get_data()

    style = message.text

    prompt = f"""
Ти професійний AI асистент.

Напиши коротке готове повідомлення.

Отримувач:
{data['target']}

Причина:
{data['reason']}

Стиль:
{style}

Правила:
- українською мовою
- природньо
- без роботизованого стилю
- коротко та переконливо
- з доречними емодзі
- тільки готовий текст повідомлення
"""

    try:

        async with ChatActionSender.typing(
            bot=bot,
            chat_id=message.chat.id
        ):

            response = client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            text = response.choices[0].message.content

            if len(text) > 4000:
                text = text[:4000]

            await message.answer(
                f"📋 Ваше повідомлення готове:\n\n{text}",
                reply_markup=make_kb([
                    "🔄 Створити ще"
                ])
            )

    except Exception as e:

        await message.answer(
            f"❌ Помилка:\n{str(e)}"
        )

    await state.clear()

# ================= MAIN =================
async def main():

    print("================================")
    print("БОТ ЗАПУЩЕНИЙ 🚀")
    print("================================")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())