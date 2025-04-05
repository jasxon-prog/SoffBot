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


load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID_1 = -1002451039792
GROUP_CHAT_ID_2 = -1002696109474
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="O'zbek"), KeyboardButton(text="Rus"), KeyboardButton(text="Ingliz")]
        ],
        resize_keyboard=True, one_time_keyboard=True
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
    await message.answer("Buyurtma kategoriyasini tanlang:", reply_markup=category_btns())
    await state.set_state(OrderState.category)

@dp.message(OrderState.category)
async def set_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Buyurtma tavsifini kiriting:")
    await state.set_state(OrderState.description)


@dp.message(OrderState.description)
async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Buyurtma tilini kiriting:", reply_markup=language_btns())
    await state.set_state(OrderState.language)

@dp.message(OrderState.language)
async def set_language(message: types.Message, state: FSMContext):
    await state.update_data(language=message.text)
    await message.answer("Buyurtma narxini kiriting:")
    await state.set_state(OrderState.price)


@dp.message(OrderState.price)
async def set_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        
        if price < 5000:
            await message.reply("❌ Narx 5000 dan kam bo‘lmasligi kerak!")
            return  # Narx 5000 dan kam bo‘lsa, keyingi qadamga o‘tmaslik

        await state.update_data(price=price)
        await message.answer("Buyurtma muddati (YYYY-MM-DD HH:MM formatida):")
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


# 📦 Buyurtmalarim komandasini qo‘shish
@dp.message(F.text == "📦 Buyurtmalarim")
async def cmd_buyurtmalarim(message: types.Message):
    user_id = message.from_user.id
    orders = get_orders_by_buyer(user_id)  # Database function to fetch orders by user_id

    if orders:
        response = "Sizning buyurtmalaringiz:\n\n"
        for order in orders:
            order_id = order[0]  # order[0] - order ID
            status = order[6]  # order[6] - status
            if status == 'Qabul qilingan':
                response += f"Buyurtma #{order_id}: Fayl jonatish kutulmoqda.\n"
            else:
                response += f"Buyurtma #{order_id}: To‘lov qilinmagan, to‘lov qilingandan so‘ng sizga fayl yuboriladi.\n"
            
            # Check if the message exceeds the limit
            if len(response) > 4000:
                await message.answer(response)  # Send the current part
                response = ""  # Reset the response

        # Send the remaining part of the response if there is any
        if response:
            await message.answer(response)

    else:
        await message.answer("Sizda hech qanday buyurtma mavjud emas.")



@dp.message(OrderState.deadline)
async def set_deadline(message: types.Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        
        # Hozirgi vaqtni olish
        current_time = datetime.now()

        # Agar kiritilgan vaqt hozirgi vaqtdan oldin bo'lsa, ogohlantirish yuborish
        if deadline < current_time:
            await message.reply("❌ Xato! Kiritilgan vaqt hozirgi vaqtdan oldin bo'la olmaydi. Iltimos, kelajakdagi vaqtni kiriting.")
            return  

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
        await message.reply("❌ Xato! Iltimos, YYYY-MM-DD HH:MM formatida kiriting.")

# ✅ Jo‘natish tugmasi bosilganda
@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[1])

    await send_order_to_group(order_id, GROUP_CHAT_ID_1, callback.from_user.id)

    asyncio.create_task(schedule_order_repost(order_id))


    await state.clear()

# ✏️ Tahrirlash tugmasi bosilganda
@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Iltimos, buyurtma ma’lumotlarini qayta kiriting.",reply_markup=category_btns())
    await state.set_state(OrderState.category)  # Boshlang‘ich state ga qaytarish


# ✅ Sotuvchi buyurtmani qabul qilganda
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order_callback(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    buyer_id = int(callback_query.data.split("_")[2])
    seller_id = callback_query.from_user.id 
    order = get_order_by_id(order_id)

    if not order:
        await callback_query.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return

    buyer_id = order[7]
    if seller_id == buyer_id:
        await callback_query.answer("❌ O‘z buyurtmangizni qabul qila olmaysiz!", show_alert=True)
        return

    accept_order(order_id, seller_id)
    accepted_orders[buyer_id] = seller_id  # Xaridor va sotuvchini bog‘lash

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

# @dp.callback_query(F.data.startswith("offer_"))
# async def offer_order_callback(callback_query: types.CallbackQuery):
#     order_id = int(callback_query.data.split("_")[1])
#     seller_id = callback_query.from_user.id

#     # Sotuvchi oldin taklif berganini tekshiramiz
#     if seller_id in user_offer_data and user_offer_data[seller_id]["order_id"] == order_id:
#         await callback_query.answer("⚠️ Siz allaqachon bu buyurtmaga taklif bergansiz!", show_alert=True)
#         return

#     # Sotuvchining yangi taklifini saqlaymizMessage
#     user_offer_data[seller_id] = {
#         "order_id": order_id,
#         "seller_id": seller_id,
#         "waiting_for_money": True 
#     }

#     await callback_query.answer()

#     await bot.send_message(
#         chat_id=seller_id,
#         text="💰 O'z narxingizni kiriting:"
#     )



@dp.callback_query(F.data.startswith("offer_"))
async def offer_order_callback(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[1])
    seller_id = callback_query.from_user.id

    # Buyurtmaning statusini tekshirish
    order_status = get_order_status(order_id)

    if order_status and order_status[0] == "Qabul qilingan":
        await callback_query.answer("❌ Buyurtma allaqachon qabul qilingan, yangi taklif berish mumkin emas.", show_alert=True)
        return

    # Buyurtma qabul qilishni faqat birinchi sotuvchi amalga oshirishi kerak
    if order_status and order_status[0] == "Ochiq":
        # Buyurtma qabul qilinishi bilan, boshqa sotuvchilarni cheklash
        update_order_status(order_id, 'Qabul qilingan', seller_id)

        # Boshqa sotuvchilarga buyurtma allaqachon qabul qilinganini xabar qilish
        for user in user_offer_data:
            if user != seller_id:
                await bot.send_message(
                    chat_id=user,
                    text=f"❌ Buyurtma {order_id} allaqachon qabul qilindi. Yangi taklif berish mumkin emas."
                )

        # Taklif va qabul qilish tugmalarini olib tashlash
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None  # Tugmalarni olib tashlash
        )

        # Qabul qilishni muvaffaqiyatli amalga oshirgandan so'ng
        await callback_query.answer("✅ Siz buyurtmani qabul qildingiz!")

        # Sotuvchiga narxni kiritish uchun so'rov yuborish
        await bot.send_message(
            chat_id=seller_id,
            text="💰 O'z narxingizni kiriting:"
        )
        return

    # Sotuvchi oldin taklif berganini tekshiramiz
    if seller_id in user_offer_data:
        # Agar sotuvchi buyurtmani tasdiqlagan bo'lsa, yangi taklif berishga ruxsat bermaymiz
        if user_offer_data[seller_id]["order_id"] == order_id and not user_offer_data[seller_id]["waiting_for_money"]:
            await callback_query.answer("❌ Siz ushbu buyurtmaga taklif bera olmaysiz, chunki buyurtma qabul qilingan.", show_alert=True)
            return
        
        # Sotuvchi oldin taklif bergan bo'lsa, uni cheklash
        if user_offer_data[seller_id]["order_id"] == order_id:
            await callback_query.answer("⚠️ Siz allaqachon bu buyurtmaga taklif bergansiz!", show_alert=True)
            return

    # Sotuvchining yangi taklifini saqlaymiz
    user_offer_data[seller_id] = {
        "order_id": order_id,
        "seller_id": seller_id,
        "waiting_for_money": True  # Taklif qabul qilinishini kutyapti
    }

    await callback_query.answer()

    # Sotuvchiga narxni kiritish uchun so'rov yuborish
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
        text=f"📝 Taklif: {money} so'm\nIzoh: {comment}\n\nTasdiqlang yoki tahrirlang.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "confirmoffer")
async def confirm_offer_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    seller_id = callback.from_user.id
    money = data.get("money")
    comment = data.get("comment")

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

    # Buyurtmachiga yuborish
    await bot.send_message(
        chat_id=buyer_id,
        text="📢 *Yangi takliflar!* \n\nTakliflar ro‘yxatini ko‘rib chiqing va keraklisini tanlang.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

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
from aiogram.types import LabeledPrice, PreCheckoutQuery


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
    

def send_file_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Faylni jo‘natish", callback_data=f"send_file:{user_id}")]
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












@dp.callback_query(F.data.startswith("acceptoffer_"))
async def handle_offer_acceptance(callback: types.CallbackQuery):
    try:
        parts = callback.data.split("_")
        order_id = int(parts[1])  # Order ID to'g'ri indeksda
        seller_id = int(parts[2])  # Seller ID to'g'ri indeksda
    except (IndexError, ValueError):
        await callback.message.answer("❌ Callback ma'lumotlari noto‘g‘ri.")
        return

    selected_offer = next(
    (offer for offer in offers if str(offer["order_id"]) == str(order_id) and int(offer["seller_id"]) == seller_id),
    None    )
    


    price = selected_offer["money"]  # Taklif summasise
    
    buyer_id = callback.from_user.id
    accepted_orders[buyer_id] = seller_id

    # To'lovni boshlash
    await create_payment(price, buyer_id)  # Bu yerda buyer IDsi va price ni uzatamiz


    # Sotuvchiga xabar yuborish
    try:
        await bot.send_message(
            seller_id,
            f"✅ Siz {order_id} raqamli buyurtmani qabul qildingiz!\n"
            f"💳 To'lov qabul qilinganidan so'ng ishni boshlashingiz mumkin."
        )
    except Exception as e:
        await callback.message.answer("❌ Sotuvchiga xabar yuborishda xatolik yuz berdi.")



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
