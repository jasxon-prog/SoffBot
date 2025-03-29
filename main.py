import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.types import Message
from aiogram import F

from aiogram.fsm.storage.memory import MemoryStorage
from database import create_tables, add_order
from dotenv import load_dotenv
import os
from aiogram.fsm.storage.memory import MemoryStorage


load_dotenv()
# 🔑 Telegram bot tokeni va guruh ID
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID_1 = int(os.getenv("GROUP_CHAT_ID_1"))  # 1-guruh ID
GROUP_CHAT_ID_2 = int(os.getenv("GROUP_CHAT_ID_2"))  # 2-guruh ID

# 🤖 Bot va Dispatcher obyektlari
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ✅ Qabul qilingan buyurtmalarni saqlash
accepted_orders = set()

# 🏁 FSM - Buyurtma bosqichlari
class OrderState(StatesGroup):
    academic_work = State()
    work_type = State()
    work_size = State()
    language = State()
    requirements = State()
    duration = State()
    price = State()
    comment = State()

class FileSendState(StatesGroup):
    waiting_for_file = State()

# 🔘 Tugmalar

def reply_start_btns():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛒 Buyurtma berish')],
            [KeyboardButton(text='📦 Buyurtmalarim')],
            [KeyboardButton(text='💳 To‘lov qilish')],
            [KeyboardButton(text='📞 Admin bilan bog‘lanish')]
        ],
        resize_keyboard=True
    )

def work_type_btns():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='1️⃣ Kurs ishi')], [KeyboardButton(text='2️⃣ Slayd')],
        [KeyboardButton(text='3️⃣ Mustaqil ish')]
    ], resize_keyboard=True)

def language_btns():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="O'zbek")], [KeyboardButton(text="Rus")],
        [KeyboardButton(text="Ingliz")]
    ], resize_keyboard=True)

def dedline_btns():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Zudlik bilan")], [KeyboardButton(text="3 kun")],
        [KeyboardButton(text="1 hafta")]
    ], resize_keyboard=True)

def accept_order_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_order:{user_id}")]
        ]
    )

def send_file_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Faylni jo‘natish", callback_data=f"send_file:{user_id}")]
        ]
    )

accepted_orders = {}  # Bu joyda e'lon qilish kerak

# 📤 Buyurtmani guruhga yuborish
async def send_order_to_group(order_text: str, user_id: int):
    try:
        message = await bot.send_message(
            chat_id=GROUP_CHAT_ID_1,
            text=order_text,
            parse_mode="Markdown",
            reply_markup=accept_order_keyboard(user_id)
        )
        
        await asyncio.sleep(300)  # 5 daqiqa kutish
        
        if user_id not in accepted_orders:
            await bot.send_message(
                chat_id=GROUP_CHAT_ID_2,
                text=order_text,
                parse_mode="Markdown",
                reply_markup=accept_order_keyboard(user_id)
            )
    except Exception as e:
        print(f"⚠ Xatolik yuz berdi: {e}")

# ✅ Buyurtmani qabul qilish
@dp.callback_query(F.data.startswith("accept_order"))
async def accept_order(callback: types.CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])  # Xaridor ID si
    seller_id = callback.from_user.id  # Sotuvchi ID si
    
    accepted_orders[buyer_id] = seller_id  # Xaridor -> Sotuvchi bog'lanishi saqlanadi
    
    # Sotuvchiga fayl yuborish tugmasi bilan xabar
    await bot.send_message(
        chat_id=seller_id,
        text="🎉 *Siz buyurtmani qabul qildingiz!* Endi faylni jo'natishingiz mumkin.",
        parse_mode="Markdown",
        reply_markup=send_file_keyboard(buyer_id)
    )

    # Xaridorga buyurtmasi qabul qilinganini bildirish
    await bot.send_message(
        chat_id=buyer_id,
        text="📩 *Buyurtmangiz qabul qilindi va tez orada sizga yuboriladi!*",
        parse_mode="Markdown"
    )

    await callback.answer("Buyurtma qabul qilindi ✅")

# 📤 Fayl jo'natish bosqichi
@dp.callback_query(F.data.startswith("send_file"))
async def ask_for_file(callback: types.CallbackQuery, state: FSMContext):
    buyer_id = int(callback.data.split(":")[1])  # Xaridor ID si
    await state.update_data(buyer_id=buyer_id)  # ✅ Xaridor ID ni saqlaymiz
    
    # Xaridorga "Fayl jo‘natilmoqda..." degan xabar boradi
    await bot.send_message(
        chat_id=buyer_id,
        text="⏳ *Fayl jo‘natilmoqda...*",
        parse_mode="Markdown"
    )
    
    await bot.send_message(
        chat_id=callback.from_user.id,  # ✅ Sotuvchi fayl yuborishi kerak
        text="📂 *Faylni yuboring:*",
        parse_mode="Markdown"
    )
    await state.set_state(FileSendState.waiting_for_file)

# 📤 Faylni qabul qilish va mijozga yuborish
@dp.message(FileSendState.waiting_for_file, F.document)
async def receive_and_forward_file(message: Message, state: FSMContext):
    data = await state.get_data()
    buyer_id = data["buyer_id"]  # ✅ To'g'ri xaridorni olamiz

    await bot.send_document(
        chat_id=buyer_id,  # ✅ Fayl to‘g‘ri odamga boradi
        document=message.document.file_id,
        caption="📩 *Buyurtmangiz fayli keldi!*",
        parse_mode="Markdown"
    )
    await message.reply("✅ *Fayl mijozga yuborildi!*", parse_mode="Markdown")
    await state.clear()


# ✅ Buyurtmani qabul qilish
@dp.callback_query(lambda call: call.data.startswith("accept_order"))
async def accept_order(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    accepted_orders.add(user_id)
    await bot.send_message(chat_id=user_id, text="🎉 *Buyurtmangiz qabul qilindi!*", parse_mode="Markdown")
    await callback.answer("Buyurtma qabul qilindi ✅")

# 🎛 Start kommandasi
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.reply(
        text="👋 Assalomu alaykum! Buyurtma berish uchun menyudan tanlang:",
        reply_markup=reply_start_btns()
    )

# 🛒 Buyurtma jarayoni
@dp.message(lambda message: message.text == "🛒 Buyurtma berish")
async def order_state(message: types.Message, state: FSMContext):
    await message.reply("📚 *Ilmiy ish turi:*", parse_mode="Markdown", reply_markup=work_type_btns())
    await state.set_state(OrderState.academic_work)

@dp.message(OrderState.academic_work)
async def get_academic_work(message: types.Message, state: FSMContext):
    await state.update_data(academic_work=message.text)
    await message.reply("📝 *Ish mavzusi:*", parse_mode="Markdown")
    await state.set_state(OrderState.work_type)

@dp.message(OrderState.work_type)
async def get_work_type(message: types.Message, state: FSMContext):
    await state.update_data(work_type=message.text)
    await message.reply("📄 *Ish hajmi:*", parse_mode="Markdown")
    await state.set_state(OrderState.work_size)

@dp.message(OrderState.work_size)
async def get_language(message: types.Message, state: FSMContext):
    await state.update_data(work_size=message.text)
    await message.reply("🗣 *Til:*", parse_mode="Markdown", reply_markup=language_btns())
    await state.set_state(OrderState.language)

@dp.message(OrderState.language)
async def get_requirements(message: types.Message, state: FSMContext):
    await state.update_data(language=message.text)
    await message.reply("📑 *Ish uchun talablar:*", parse_mode="Markdown")
    await state.set_state(OrderState.requirements)

@dp.message(OrderState.requirements)
async def get_duration(message: types.Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await message.reply("⏳ *Muddat:*", parse_mode="Markdown", reply_markup=dedline_btns())
    await state.set_state(OrderState.duration)

@dp.message(OrderState.duration)
async def get_price(message: types.Message, state: FSMContext):
    await state.update_data(duration=message.text)
    await message.reply("💰 *Byudjet:*", parse_mode="Markdown")
    await state.set_state(OrderState.price)

@dp.message(OrderState.price)
async def get_comment(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)  # Kiritilgan qiymatni integerga o'tkazamiz
        if price < 5000:
            await message.reply("❌ Minimal byudjet 5000 so‘m bo‘lishi kerak! Qayta kiriting.")
            return  # Ushbu bosqichda to‘xtaymiz, yangi davlat holatiga o‘tmaymiz

        await state.update_data(price=price)
        await message.reply("📝 *Qo‘shimcha izoh:*", parse_mode="Markdown")
        await state.set_state(OrderState.comment)

    except ValueError:
        await message.reply("❌ Iltimos, faqat raqam kiriting! Qayta urinib ko‘ring.")

@dp.message(OrderState.comment)
async def finish_order(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()

    order_data = {
        "academic_work": data["academic_work"],
        "work_type": data["work_type"],
        "work_size": data["work_size"],
        "language": data["language"],
        "requirements": data["requirements"],
        "duration": data["duration"],
        "price": data["price"],
        "comment": data["comment"],
    }
    add_order(order_data, message.from_user.id)

    summary = "\n".join([
        f'📚 *Ilmiy ish turi:* {data["academic_work"]}',
        f'📝 *Ish mavzusi:* {data["work_type"]}',
        f'📄 *Hajmi:* {data["work_size"]}',
        f'🗣 *Til:* {data["language"]}',
        f'📑 *Talablar:* {data["requirements"]}',
        f'⏳ *Muddat:* {data["duration"]}',
        f'💰 *Byudjet:* {data["price"]}',
        f'📝 *Qo‘shimcha izoh:* {data["comment"]}',
        f'🚀 *Yangi buyurtma qabul qilindi!*'
    ])

    await message.reply(text="⏳ *Buyurtmangiz qabul qilinmoqda...*", parse_mode="Markdown")
    await send_order_to_group(summary, message.from_user.id)
    await state.clear()

# 🔄 Botni ishga tushirish
async def main():
    create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())