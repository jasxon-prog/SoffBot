import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
)
from aiogram.types import Message
from aiogram import F
from datetime import datetime
from aiogram.fsm.storage.memory import MemoryStorage
from database import create_tables, add_order,get_user_orders
from dotenv import load_dotenv
import os
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()
# 🔑 Telegram bot tokeni va guruh ID
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID_1 = int(os.getenv("GROUP_CHAT_ID_1"))  # 1-guruh ID
GROUP_CHAT_ID_2 = int(os.getenv("GROUP_CHAT_ID_2"))  # 2-guruh ID
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

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
        resize_keyboard=True,
        one_time_keyboard=True  # ✅ One-time keyboard qo'shildi
    )

def work_type_btns():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='1️⃣ Kurs ishi')],
            [KeyboardButton(text='2️⃣ Slayd')],
            [KeyboardButton(text='3️⃣ Mustaqil ish')]
        ],
        resize_keyboard=True,
        one_time_keyboard=True  # ✅ One-time keyboard qo'shildi
    )

def language_btns():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="O'zbek")],
            [KeyboardButton(text="Rus")],
            [KeyboardButton(text="Ingliz")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True  # ✅ One-time keyboard qo'shildi
    )

def dedline_btns():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Zudlik bilan")],
            [KeyboardButton(text="3 kun")],
            [KeyboardButton(text="1 hafta")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True  # ✅ One-time keyboard qo'shildi
    )

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

async def remind_seller(seller_id: int, buyer_id: int):
    while buyer_id in accepted_orders:
        await asyncio.sleep(3600)  # 1 soat kutish
        await bot.send_message(
            chat_id=seller_id,
            text="⏳ *Sizning xaridoringiz hali faylni kutmoqda!*",
            parse_mode="Markdown"
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

# 💳 To‘lovni boshlash
async def create_payment(price, user_id):
    prices = [LabeledPrice(label="Ilmiy ish buyurtmasi", amount=price * 100)]  # So‘mni tiyin/sentga o‘girish
    await bot.send_invoice(
        chat_id=user_id,
        title="Ilmiy ish buyurtmasi",
        description="Sizning ilmiy ish buyurtmangiz uchun to‘lov.",
        payload=f"order_{user_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=prices,
        start_parameter="buy_order"
    )

@dp.callback_query(F.data.startswith("accept_order"))
async def accept_order(callback: types.CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])  # Buyurtma bergan foydalanuvchi ID si
    seller_id = callback.from_user.id  # Buyurtmani qabul qilgan foydalanuvchi ID si

    # 🔴 Foydalanuvchi o‘z buyurtmasini qabul qila olmasligi kerak
    if buyer_id == seller_id:
        await callback.answer("❌ Siz o'zingiz bergan buyurtmani qabul qila olmaysiz!", show_alert=True)
        return

    # ✅ Buyurtmani qabul qilish jarayoni
    accepted_orders[buyer_id] = seller_id  

    # Buyurtma beruvchiga xabar yuborish
    await bot.send_message(
        chat_id=buyer_id,
        text="✅ *Buyurtmangiz qabul qilindi!* To‘lovni amalga oshirsangiz, fayl sizga yuboriladi.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 To‘lov qilish", callback_data=f"pay_now:{buyer_id}")]
            ]
        )
    )

    # Buyurtmani qabul qilgan foydalanuvchiga xabar yuborish
    await bot.send_message(
        chat_id=seller_id,
        text="🎉 *Siz buyurtmani qabul qildingiz!* To‘lov amalga oshirilishini kuting.",
        parse_mode="Markdown"
    )

    await callback.answer("Buyurtma qabul qilindi ✅")


    await bot.send_message(
        chat_id=seller_id,
        text="🎉 *Siz buyurtmani qabul qildingiz!* To‘lov amalga oshirilishini kuting.",
        parse_mode="Markdown"
    )

    await callback.answer("Buyurtma qabul qilindi ✅")

# 💳 Xaridor to'lov qilish tugmasini bossagina invoice yuboriladi
@dp.callback_query(F.data.startswith("pay_now"))
async def process_payment(callback: types.CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])
    order_data = get_user_orders(buyer_id)  
    
    if not order_data:
        await callback.message.reply("❌ Buyurtma topilmadi.")
        return
    
    total_price = int(order_data[-1][7])  # Oxirgi buyurtma summasini olish
    await create_payment(total_price, buyer_id)  
    await callback.answer("To‘lov oynasi ochildi ✅")

# ✅ To‘lovni tasdiqlash
@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ✅ Muvaffaqiyatli to‘lovdan keyin sotuvchiga xabar yuborish
@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    buyer_id = message.from_user.id
    seller_id = accepted_orders.get(buyer_id)

    if seller_id:
        await bot.send_message(
            chat_id=seller_id,
            text="✅ *To‘lov amalga oshirildi!* Endi faylni xaridorga jo‘natishingiz mumkin.",
            parse_mode="Markdown",
            reply_markup=send_file_keyboard(buyer_id)
        )

    await message.reply("✅ To‘lov muvaffaqiyatli amalga oshirildi! Fayl jo‘natilishi kutilmoqda.")

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
    buyer_id = data["buyer_id"]

    await bot.send_document(
        chat_id=buyer_id,
        document=message.document.file_id,
        caption="📩 *Buyurtmangiz fayli keldi!*",
        parse_mode="Markdown"
    )

    await message.reply("✅ *Fayl mijozga yuborildi!*", parse_mode="Markdown")

    # Sotuvchiga eslatma yuborishni to‘xtatish
    if buyer_id in accepted_orders:
        del accepted_orders[buyer_id]

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
    await message.reply("⏳ *Muddatni kiriting (YYYY-MM-DD HH:MM formatida):*", parse_mode="Markdown")
    await state.set_state(OrderState.duration)

@dp.message(OrderState.duration)
async def get_price(message: types.Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        now = datetime.now()
        if deadline <= now:
            await message.reply("❌ Noto‘g‘ri vaqt! Faqat kelajakdagi vaqtni kiriting.")
            return
        
        await state.update_data(duration=deadline.strftime("%Y-%m-%d %H:%M"))
        await message.reply("💰 *Byudjet:*", parse_mode="Markdown")
        await state.set_state(OrderState.price)

    except ValueError:
        await message.reply("❌ *Xato!* Iltimos, vaqtni quyidagi formatda kiriting: `YYYY-MM-DD HH:MM`", parse_mode="Markdown")

@dp.message(OrderState.price)
async def get_comment(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)  # Kiritilgan qiymatni integerga o'tkazamiz
        if price < 1000:
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