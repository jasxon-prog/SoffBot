import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton,Message
)
from datetime import datetime
from dotenv import load_dotenv
from database import *
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.types import CallbackQuery


load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID_1 = -1002451039792
GROUP_CHAT_ID_2 = -1002696109474
GROUP_CHAT_ID_ADMIN = -1002276366884
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


bot = Bot(token=TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    category = State()
    description = State()
    language = State()
    price = State()
    deadline = State()
    status = State()

class OfferState(StatesGroup):
    money = State()
    comment = State()

def category_btns():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Kurs ishlari | Kompyuter grafika"), KeyboardButton(text="Kurs ishlari | Ona tili")],
        [KeyboardButton(text="Dissertatsiya ishlari | Logistika"), KeyboardButton(text="Video materiallar | Kompyuter grafika")],
        [KeyboardButton(text="Plakatlar | Logistika"), KeyboardButton(text="Testlar | Logistika")],
        [KeyboardButton(text="Taqdimotlar | Ona tili"), KeyboardButton(text="Taqdimotlar | Ona tili o'qitish metodikasi")],
        [KeyboardButton(text="Labaratoriya Ishlari | Logistika"), KeyboardButton(text="Diplom ishlari | Kompyuter grafika")]
    ], resize_keyboard=True, one_time_keyboard=True)


def reply_start_btns():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛒 Buyurtma berish')],
            [KeyboardButton(text='📦 Buyurtmalarim')],
            [KeyboardButton(text='📞 Admin bilan bog‘lanish')]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

def language_btns():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
            ]
        ]
    )

# Buyurtma yangilanishini yoki eslatmalarni rejalashtirish funksiyasi
async def schedule_order_repost(order_id):
    await asyncio.sleep(30)  # 5 daqiqa kutish

    order = get_order_by_id(order_id)
    if order and order[6] == "Ochiq":  # Buyurtma hali qabul qilinmaganligini tekshiramiz
        await send_order_to_group(order_id, GROUP_CHAT_ID_2)  # Ikkinchi guruhga yuborish


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.reply("👋 Assalomu alaykum! Buyurtma berish uchun menyudan tanlang:", reply_markup=reply_start_btns())

@dp.message(F.text == "🛒 Buyurtma berish")
async def new_order_start(message: types.Message, state: FSMContext):
    await message.answer("📂 Buyurtmangiz tegishli bo‘lgan kategoriyani tanlang:", reply_markup=category_btns())
    await state.set_state(OrderState.category)

@dp.message(OrderState.category)
async def set_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("📝 Buyurtma tavsifini kiriting (misol uchun: 'Kichik reklama matni tayyorlash'):")
    await state.set_state(OrderState.description)


@dp.message(OrderState.description)
async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("🌐 Buyurtmangiz qaysi tilda tayyorlanishini xohlaysiz? Tilni tanlang:", reply_markup=language_btns())
    await state.set_state(OrderState.language)


@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]

    lang_map = {
        "uz": "O'zbek",
        "en": "English",
        "ru": "Русский"
    }
    language = lang_map.get(lang_code, "Noma'lum")

    await state.update_data(language=language)

    await callback.message.edit_reply_markup()
    await callback.message.answer("💰 Buyurtma narxini kiriting:")
    await state.set_state(OrderState.price)


@dp.message(OrderState.price)
async def set_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        
        if price < 5000:
            await message.reply("❌ Narx 5000 dan kam bo‘lmasligi kerak!")
            return 
        await state.update_data(price=price)
        await message.answer("⏳ Iltimos, buyurtma muddati uchun necha kun kerakligini kiriting (faqat son).\n\nMasalan: 5")
        await state.set_state(OrderState.deadline)
    except ValueError:
        await message.reply("❌ Iltimos, faqat raqam kiriting!")

# ✅ Buyurtmani tasdiqlash yoki tahrirlash tugmalari
def confirmation_buttons(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Jo‘natish", callback_data=f"confirm_{order_id}")],
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_{order_id}")]
        ]
    )

ADMIN_PHONE = "+998901234567"  # bu yerga admin raqamini yozing

@dp.message(F.text == "📞 Admin bilan bog‘lanish")
async def send_admin_contact(message: types.Message):
    await message.answer(
        text=f"📞 Admin bilan bog‘lanish uchun:\n\nTelefon raqami: {ADMIN_PHONE}",
        reply_markup=reply_start_btns()
    )





@dp.message(F.text == "📦 Buyurtmalarim")
async def cmd_buyurtmalarim(message: types.Message):
    user_id = message.from_user.id

    # First, check if the user is a buyer or a seller
    orders = get_orders_by_buyer(user_id)  # Attempt to get orders as a buyer

    if not orders:  # If no orders found as a buyer, try fetching as a seller
        orders = get_orders_by_seller(user_id)

    if not orders:
        await message.answer("📭 Sizda hech qanday buyurtma mavjud emas.")
        return

    for order in orders:
        order_id = order[0]
        category = order[1]
        description = order[2]
        language = order[3]
        price = order[4]
        deadline = order[5]
        status = order[6]

        # Holat bo‘yicha matn
        if status == 'Qabul qilingan':
            holat_text = "✅ Qabul qilingan "
        else:
            holat_text = "❌ Ochiq — To‘lov qilinmagan"

        # Buyurtma matni
        text = f"""📦 <b>Buyurtma #{order_id}</b>
                    📂 <b>Kategoriya:</b> {category}
                    📝 <b>Tavsif:</b> {description}
                    🌐 <b>Til:</b> {language}
                    💰 <b>Narx:</b> {price} so‘m
                    ⏰ <b>Muddat:</b> {deadline}
                    📍 <b>Status:</b> {holat_text}
                    """

        await message.answer(text, parse_mode="HTML")


from datetime import datetime, timedelta

@dp.message(OrderState.deadline)
async def set_deadline(message: types.Message, state: FSMContext):
    try:
        days = int(message.text.strip())

        if days <= 0:
            await message.reply("❌ Xato! Iltimos, 1 yoki undan katta kun kiriting.")
            return

        deadline = datetime.now() + timedelta(days=days)

        await state.update_data(deadline=deadline.strftime("%Y-%m-%d %H:%M"))

        data = await state.get_data()
        data["status"] = "Ochiq"

        order_id = add_order(data, message.from_user.id)

        text = f"📌 *Buyurtmangizni tekshiring!*\n"\
               f"🆔 Buyurtma ID: {order_id}\n"\
               f"📌 Kategoriya: {data['category']}\n"\
               f"💬 Tavsif: {data['description']}\n"\
               f"📝 Til: {data['language']}\n"\
               f"💰 Narx: {data['price']} so‘m\n"\
               f"⏳ Muddat: {data['deadline']}\n"\
               f"📌 Holati: *{data['status']}*\n\n"\
               "❗ Iltimos, ma’lumotlarni tasdiqlang yoki tahrirlang."

        await message.answer(text, reply_markup=confirmation_buttons(order_id), parse_mode="Markdown")
        await state.clear()

    except ValueError:
        await message.reply("❌ Iltimos, necha kunda topshirilishi kerakligini faqat son bilan kiriting (masalan: 5).")







@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[1])

    # 🧼 Tugmalarni olib tashlash
    await callback.message.edit_reply_markup(reply_markup=None)

    # Buyurtmani guruhga yuborish
    await send_order_to_group(order_id, GROUP_CHAT_ID_1, callback.from_user.id)

    # Repost qilish uchun background task
    asyncio.create_task(schedule_order_repost(order_id))

    await state.clear()


# ✏️ Tahrirlash tugmasi bosilganda
@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✏️ Iltimos, buyurtma ma’lumotlarini qayta kiriting.",reply_markup=category_btns())
    await state.set_state(OrderState.category)  # Boshlang‘ich state ga qaytarish


@dp.callback_query(F.data.startswith("accept_"))
async def accept_order_callback(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    buyer_id = int(callback_query.data.split("_")[2])
    seller_id = callback_query.from_user.id 
    order = get_order_by_id(order_id)

    if not order:
        await callback_query.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    # Buyurtma qabul qilinishini tekshirish
    if order[6] == "Qabul qilingan":
        await callback_query.answer("❌ Bu buyurtma allaqachon qabul qilingan!", show_alert=True)
        return

    # Sotuvchi o'zining buyurtmasini qabul qila olmaydi
    if seller_id == buyer_id:
        await callback_query.answer("❌ O‘z buyurtmangizni qabul qila olmaysiz!", show_alert=True)
        return

    # Buyurtma qabul qilish
    accept_order(order_id, seller_id)
    update_order_status(order_id, 'Qabul qilingan', seller_id)  # Buyurtmaning holatini yangilash
    accepted_orders[buyer_id] = (seller_id, order_id) # Xaridor va sotuvchini bog‘lash

    # Xaridorga xabar va to‘lov tugmasini yuborish
    await bot.send_message(
        chat_id=buyer_id, 
        text="✅ Buyurtmangiz qabul qilindi! Endi to‘lovni amalga oshiring.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 To‘lov qilish", callback_data=f"pay_now:{buyer_id}")]
            ]
        )
    )

    # Sotuvchiga tasdiqlash xabari yuborish
    await bot.send_message(
        chat_id=seller_id,
        text="⚠️ Buyurtmani qabul qildingiz. To‘lov amalga oshgandan keyin ishni boshlang!"
    )

    await callback_query.answer("✅ Buyurtma qabul qilindi!")




async def send_order_to_group(order_id, group_id, user_id=None):
    order = get_order_by_id(order_id)
    if order:
        text = f"📌 *Yangi buyurtma!*\n"\
               f"🆔 Buyurtma ID: {order[0]}\n"\
               f"📌 Kategoriya: {order[1]}\n"\
               f"💬 Tavsif: {order[2]}\n"\
               f"📝 Til: {order[3]}\n"\
               f"💰 Buyurtmachining narxi: {order[4]}\n"\
               f"⏳ Muddat: {order[5]}\n"\
               f"📌 Holati: *{order[6]}*"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{order_id}_{user_id}")],
                [InlineKeyboardButton(text="📩 Taklif berish", callback_data=f"offer_{order_id}")]
            ]
        )

        # Buyurtmani guruhga yuborish
        await bot.send_message(chat_id=group_id, text=text, reply_markup=keyboard, parse_mode="Markdown")

        # Xaridorga faqat kerakli mutaxassislarga yuborilganligi haqida xabar berish
        if user_id:
            await bot.send_message(chat_id=user_id, text="✅ Buyurtmangiz kerakli mutaxassislarga yuborildi, qabul qilishni kuting!")
        




user_offer_data = {}

@dp.callback_query(F.data.startswith("offer_"))
async def offer_order_callback(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    seller_id = callback_query.from_user.id

    # Sotuvchi oldin taklif berganini tekshiramiz
    if seller_id in user_offer_data and user_offer_data[seller_id]["order_id"] == order_id:
        await callback_query.answer("⚠️ Siz allaqachon bu buyurtmaga taklif bergansiz!", show_alert=True)
        return

    # Sotuvchining yangi taklifini saqlaymizMessage
    user_offer_data[seller_id] = {
        "order_id": order_id,
        "seller_id": seller_id,
        "waiting_for_money": True 
    }

    await callback_query.answer()

    await bot.send_message(
        chat_id=seller_id,
        text="💰 O'z narxingizni kiriting:"
    )











@dp.message(
    F.chat.type == "private",
    lambda message: message.from_user.id in user_offer_data and user_offer_data[message.from_user.id].get("waiting_for_money", False)
)
async def process_money_input(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("❌ Iltimos, faqat raqam kiriting!")
        return
    
    seller_id = message.from_user.id
    money = int(message.text)
    
    user_offer_data[seller_id]["money"] = money
    user_offer_data[seller_id]["waiting_for_money"] = False
    user_offer_data[seller_id]["waiting_for_comment"] = True
    
    await state.set_state(OfferState.comment)
    await state.update_data(user_offer_data[seller_id])
    
    await message.answer("✍️ Izohingizni kiriting:")




# Takliflar ro‘yxati
offers = []  # Bu bazaga qo‘shilgan takliflarni saqlaydi


@dp.message(OfferState.comment)
async def set_offer_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        await message.reply("❌ Xatolik: Buyurtma ID topilmadi.")
        return

    order_id = data.get("order_id")
    money = data.get("money")
    comment = message.text
    seller_id = message.from_user.id

    if not order_id or not money:
        await message.reply("❌ Xatolik: Ma'lumot to‘liq emas.")
        return

    # Taklifni vaqtincha contextga saqlaymiz (hali yuborilmaydi)
    await state.update_data(comment=comment)

    # Sotuvchiga tasdiqlash xabari
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirmoffer"),
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="editoffer")
    ]])

    await bot.send_message( 
        chat_id=seller_id,
        text = (
                f"📝 *Taklif tafsilotlari:*\n"
                f"💰 Narx: *{money} so'm*\n"
                f"🗒 Izoh: _{comment}_\n\n"
                f"⚠️ *Ogohlantirish:*\n"
                f"Sizning bergan takliflaringiz administrator tomonidan tekshiriladi. "
                f"Telefon raqami yoki boshqa shaxsiy ma'lumotlarni yozish *qattiyan man etiladi!* "
                f"Aks holda sizga nisbatan chora ko‘riladi.\n\n"
                f"Quyidagi tugmalar orqali taklifni tasdiqlang yoki tahrirlang."
            ),
        reply_markup=keyboard
        )

import re

# Telefon raqami yoki emailni tekshirish uchun regex
def contains_personal_info(text: str) -> bool:
    uzbek_phone_pattern = r"(\+998|0)?\d{9}"  # +998 bilan yoki +998siz 9 raqamli telefon raqami
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"  # Email formati

    if re.search(uzbek_phone_pattern, text) or re.search(email_pattern, text):
        return True
    return False

@dp.callback_query(F.data == "confirmoffer")
async def confirm_offer_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    seller_id = callback.from_user.id
    money = data.get("money")
    comment = data.get("comment")

    seller_username = callback.from_user.username or "username yo'q"
    seller_fullname = callback.from_user.full_name

    # money va comment ni stringga aylantirish
    if contains_personal_info(str(money)) or contains_personal_info(str(comment)):
        admin_text = (
            f"⚠️ *Shubhali ma'lumot yuborildi!*\n"
            f"🧑 Sotuvchi: [{seller_fullname}](tg://user?id={seller_id})\n"
            f"📦 Buyurtma ID: {order_id}\n"
            f"💰 Narx: {money}\n"
            f"📝 Izoh: {comment}\n\n"
            f"Telefon raqami yoki email mavjud!"
        )
        await bot.send_message(chat_id=GROUP_CHAT_ID_ADMIN, text=admin_text, parse_mode="Markdown")
        await callback.message.edit_text("✅ Taklifingiz muvaffaqiyatli yuborildi.")
        await state.clear()

    else:
        # Bazaga qo‘shish
        add_offer(order_id, seller_id, money, comment)
        offers.append({
            "order_id": order_id,
            "seller_id": seller_id,
            "money": money,
            "comment": comment
        })

        # Buyurtmachining ID sini olish
        buyer_id = get_order_by_id(order_id)[7]

        # Takliflar tugmalarini yaratish
        buttons = [
            InlineKeyboardButton(
                text=f"✅ Taklif: {offer['money']} - {offer['comment']}",
                callback_data=f"select_offer_{offer['order_id']}_{offer['seller_id']}"
            )
            for offer in offers if offer['order_id'] == order_id
        ]
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[buttons[i:i + 3] for i in range(0, len(buttons), 3)]
        )

        seller_username = callback.from_user.username or "username yo'q"
        seller_fullname = callback.from_user.full_name

        # Admin guruhga yuboriladigan xabar
        admin_text = (
            f"📥 *Yangi taklif!*\n\n"
            f"🧑 Sotuvchi: [{seller_fullname}](tg://user?id={seller_id})\n"
            f"💰 Narx: {money}\n"
            f"📝 Izoh: {comment}\n"
            f"📦 Buyurtma ID: {order_id}"
        )

        await bot.send_message(chat_id=GROUP_CHAT_ID_ADMIN, text=admin_text, parse_mode="Markdown")

        # Buyurtmachiga yuborish
        await bot.send_message(
            chat_id=buyer_id,
            text="📢 *Yangi takliflar!* \n\nTakliflar ro‘yxatini ko‘rib chiqing va keraklisini tanlang.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

                # Sotuvchiga javob



        # Sotuvchiga javob
        await callback.message.edit_text("✅ Taklifingiz muvaffaqiyatli yuborildi.")
        await state.clear()



@dp.callback_query(F.data == "editoffer")
async def edit_offer_callback(callback: types.CallbackQuery, state: FSMContext):
    seller_id = callback.from_user.id

    # user_offer_data mavjudligini tekshiramiz
    if seller_id not in user_offer_data:
        await callback.message.edit_text("❌ Tahrirlashda xatolik: ma’lumot topilmadi.")
        return

    user_offer_data[seller_id]["waiting_for_money"] = True
    user_offer_data[seller_id]["waiting_for_comment"] = False

    await state.set_state(OfferState.money)
    await callback.message.edit_text("✏️ Yangi narxni kiriting:")






async def update_offer_real_time():
    while True:
        # Takliflar ro‘yxatini real-time yangilash
        await asyncio.sleep(5)  # Bu yerda 5 sekundlik intervalda yangilanadi, o'zgartirishingiz mumkin.
        
        for order in offers:
            buyer_id = get_order_by_id(order["order_id"])[7]
            inline_buttons = [
                InlineKeyboardButton(text=f"✅ Taklif: {offer['money']} - {offer['comment']}", callback_data=f"select_offer_{offer['order_id']}_{offer['seller_id']}")
                for offer in offers if offer['order_id'] == order["order_id"]
            ]
            inline_keyboard = InlineKeyboardMarkup(row_width=1)
            inline_keyboard.add(*inline_buttons)

            await bot.send_message(
                chat_id=buyer_id,
                text=f"📢 *Yangi takliflar!* \n\n"
                     f"Takliflar ro‘yxatini ko‘rib chiqing va pastdagi tugmani bosing.",
                reply_markup=inline_keyboard,
                parse_mode="Markdown"
            )




@dp.callback_query(F.data.startswith("select_offer_"))
async def handle_offer_selection(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        order_id = parts[2]
        seller_id = int(parts[3])
    except (IndexError, ValueError):
        await callback.message.answer("❌ Callback ma'lumotlari noto‘g‘ri.")
        return

    # 👇 Taklifni to'g'ri solishtirish uchun str() ishlatyapmiz
    selected_offer = next(
        (offer for offer in offers if str(offer["order_id"]) == str(order_id) and int(offer["seller_id"]) == seller_id),
        None
    )

    if not selected_offer:
        await callback.message.answer("❌ Taklif topilmadi yoki eskirgan.")
        return

    # Sotuvchini olish
    seller_user = await bot.get_chat(seller_id)
    seller_name = seller_user.full_name
    
    # Tugmalar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qabul qilish",
                    callback_data=f"acceptoffer_{order_id}_{seller_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data=f"back_to_offers_{order_id}"
                )
            ]
        ]
    )

    await callback.message.answer(
        f"👤 Taklif beruvchi: {seller_name}\n"
        f"💵 Narx: {selected_offer['money']}\n"
        f"💬 Izoh: {selected_offer['comment']}",
        reply_markup=keyboard
    )



"======================================================== TO'LOV TIZMI=========================================================="


class FileSendState(StatesGroup):
    waiting_for_file = State()

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
    

def send_file_keyboard(user_id,order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Faylni jo‘natish", callback_data=f"send_file:{user_id}:{order_id}")]
        ]
    )

accepted_orders = {}  # Bu joyda e'lon qilish kerak


# 💳 Xaridor to'lov qilish tugmasini bossagina invoice yuboriladi
@dp.callback_query(F.data.startswith("pay_now"))
async def process_payment(callback: types.CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])
    order_data = get_user_orders(buyer_id)

    if not order_data:
        await callback.message.reply("❌ Buyurtma topilmadi.")
        return
    
    total_price = int(order_data[-1][4])  # Oxirgi buyurtma summasini olish
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
    seller_id, order_id = accepted_orders.get(buyer_id, (None, None))




    if seller_id:
        await bot.send_message(
            chat_id=seller_id,
            text="✅ *To‘lov amalga oshirildi!* Endi faylni xaridorga jo‘natishingiz mumkin.",
            parse_mode="Markdown",
            reply_markup=send_file_keyboard(buyer_id,order_id)
        )

    await message.reply("✅ To‘lov muvaffaqiyatli amalga oshirildi! Fayl jo‘natilishi kutilmoqda.")





# 📤 Fayl jo'natish bosqichi
@dp.callback_query(F.data.startswith("send_file"))
async def ask_for_file(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    buyer_id = int(parts[1])
    order_id = int(parts[2]) if len(parts) > 2 else None  # Xaridor ID si
    
    await state.update_data(buyer_id=buyer_id,order_id=order_id)  # ✅ Xaridor ID ni saqlaymiz
    
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



from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Faylni qabul qilish va mijozga yuborish
@dp.message(FileSendState.waiting_for_file, F.document)
async def receive_and_forward_file(message: Message, state: FSMContext):
    data = await state.get_data()
    buyer_id = data["buyer_id"]
    order_id = data.get("order_id", "XXXX")  # order_id mavjud bo‘lmasa, XXXX bo‘ladi

    # Inline tugmalar
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash va sotuvchiga baho berish",
                callback_data=f"confirmorder_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❗ Muammo bor - Admin bilan bog‘lanish",
                callback_data="contact_admin"
            )
        ]
    ])

    # Xaridorga fayl yuborish
    await bot.send_document(
        chat_id=buyer_id,
        document=message.document.file_id,
        caption=f"✅ Siz bergan #{order_id}-RAQAM dagi buyurtmangiz yetib keldi!\n\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=buttons,
        parse_mode="Markdown"
    )

    await message.reply("✅ *Fayl mijozga yuborildi!*", parse_mode="Markdown")

    # Sotuvchiga eslatma yuborishni to‘xtatish
    if buyer_id in accepted_orders:
        del accepted_orders[buyer_id]

    await state.clear()


@dp.callback_query(F.data == "contact_admin")
async def contact_admin(callback: CallbackQuery):
    admin_info = (
        "📞 Admin bilan bog‘lanish:\n"
        "👤 Ismi: Avazbek\n"
        "📱 Telegram: @admin_username\n"
        "📞 Telefon: +998 90 123 45 67\n\n"
        "ℹ️ Eslatma: Iltimos, adminga murojaat qilayotganda avval buyurtma raqamingizni yozing, "
        "so‘ngra muammo yoki shikoyatingizni tushuntiring. Bu javob berish jarayonini tezlashtiradi."
    )

    await callback.message.answer(admin_info)
    await callback.answer()




@dp.callback_query(F.data.startswith("confirmorder"))
async def confirm_order(callback: CallbackQuery):
    try:
        order_id = int(callback.data.split("_")[1])

        # Baholash uchun tugmalar
        rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐️1", callback_data=f"rate:{order_id}:1"),
                InlineKeyboardButton(text="⭐️2", callback_data=f"rate:{order_id}:2"),
                InlineKeyboardButton(text="⭐️3", callback_data=f"rate:{order_id}:3"),
                InlineKeyboardButton(text="⭐️4", callback_data=f"rate:{order_id}:4"),
                InlineKeyboardButton(text="⭐️5", callback_data=f"rate:{order_id}:5"),
            ]
        ])

        await callback.message.answer(
            f"✅ Siz #{order_id}-ID buyurtmani tasdiqladingiz!\n\nIltimos, sotuvchiga baho bering:",
            reply_markup=rating_keyboard
        )

        await callback.answer()

    except (IndexError, ValueError):
        await callback.message.answer("❗ Buyurtma ID noto‘g‘ri ko‘rsatildi.")
        await callback.answer()


@dp.callback_query(F.data.startswith("rate:"))
async def rate_seller(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        order_id = int(parts[1])
        rating = int(parts[2])
        print(parts)
        # Buyurtma IDsi orqali sotuvchi IDni olish
        seller_id = get_seller_id_by_order(order_id)
        print(seller_id)

        if seller_id:
            # Bahoni sotuvchiga qo‘shish
            add_rating(order_id, seller_id, rating)

            # Foydalanuvchiga javob yuborish
            await callback.message.answer(
                f"🎉 Rahmat! Siz sotuvchiga ⭐️{rating}/5 baho berdingiz.\n"
                f"📦 Buyurtma ID: #{order_id}\n\n"
                "Agar sizga yana ilmiy ish kerak bo‘lsa yoki yangi buyurtma bermoqchi bo‘lsangiz, "
                "botimizni qayta ishga tushiring: /start\n\n"
                "Sifatli xizmatlar uchun bizni tanlaganingizdan mamnunmiz! 😊"
            )
            await callback.answer()

        else:
            await callback.answer("❌ Buyurtma topilmadi.")
        
    except Exception as e:
        await callback.message.answer("❗ Baho berishda xatolik yuz berdi.")
        await callback.answer()





@dp.callback_query(F.data.startswith("acceptoffer_"))
async def handle_offer_acceptance(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        order_id = int(parts[1])  # Order ID to'g'ri indeksda
        seller_id = int(parts[2])  # Seller ID to'g'ri indeksda
    except (IndexError, ValueError):
        await callback.message.answer("❌ Callback ma'lumotlari noto‘g‘ri.")
        return

    # Taklifni solishtirish
    selected_offer = next(
        (offer for offer in offers if str(offer["order_id"]) == str(order_id) and int(offer["seller_id"]) == seller_id),
        None
    )

    if not selected_offer:
        await callback.message.answer("❌ Taklif topilmadi yoki eskirgan.")
        return

    price = selected_offer["money"]  # Taklif summasini olish

    buyer_id = callback.from_user.id  # Xaridorning ID sini olish
    accepted_orders[buyer_id] = (seller_id, order_id)  # Xaridor va sotuvchini va buyurtma ID sini bog'lash

    # To'lovni boshlash
    await create_payment(price, buyer_id)  # Bu yerda buyer ID va price ni uzatamiz

    # Sotuvchiga xabar yuborish
    try:
        await bot.send_message(
            seller_id,
            f"✅ Siz {order_id} raqamli buyurtmani qabul qildingiz!\n"
            f"💳 To'lov qabul qilinganidan so'ng ishni boshlashingiz mumkin."
        )
    except Exception as e:
        await callback.message.answer("❌ Sotuvchiga xabar yuborishda xatolik yuz berdi.")

    # Xaridorga xabar yuborish
    await callback.message.answer("✅ Taklif qabul qilindi! Sotuvchiga xabar yuborildi.")


@dp.callback_query(F.data.startswith("back_to_offers_"))
async def back_to_offers(callback: types.CallbackQuery):
    try:
        await callback.message.delete()  # Faqat shu xabarni o‘chirish
    except Exception as e:
        print(f"Xabarni o‘chirishda xato: {e}")

    await callback.answer()


async def main():
    create_tables()
    await dp.start_polling(bot)
    asyncio.create_task(update_offer_real_time())



if __name__ == "__main__":
    asyncio.run(main())
