import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN
from database import init_db, add_user, get_user_balance, update_balance, save_order, get_products
from provider import send_auto_donate
from admin import admin_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

class BuyState(StatesGroup):
    waiting_for_input = State()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 PUBG Mobile", callback_data="game_pubg"),
         InlineKeyboardButton(text="🔥 Free Fire", callback_data="game_ff")],
        [InlineKeyboardButton(text="⚡️ Mobile Legends", callback_data="game_mlbb"),
         InlineKeyboardButton(text="🎯 Standoff 2", callback_data="game_standoff")],
        [InlineKeyboardButton(text="⭐ Telegram Stars & Premium", callback_data="game_telegram")],
        [InlineKeyboardButton(text="👥 Telegram Obunachilar", callback_data="game_subscribers")],
        [InlineKeyboardButton(text="💳 Balansni to'ldirish", callback_data="topup"),
         InlineKeyboardButton(text="👤 Kabinet", callback_data="cabinet")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"🌟 O'yin valyutalari, Telegram xizmatlari va obunachilarni avtomatik xarid qilish botiga xush kelibsiz.\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "cabinet")
async def user_cabinet(callback: types.CallbackQuery):
    balance = get_user_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"👤 **Sizning kabinetingiz:**\n\n"
        f"🆔 ID: `{callback.from_user.id}`\n"
        f"💰 Balansingiz: **{balance} so'm**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
        ])
    )

@dp.callback_query(F.data.startswith("game_"))
async def select_game(callback: types.CallbackQuery, state: FSMContext):
    game = callback.data.split("_")[1]
    prods = get_products(game)
    
    kb = []
    for p_id, name, price in prods:
        kb.append([InlineKeyboardButton(text=f"{name} — {price} so'm", callback_data=f"buy_{game}_{name}_{price}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")])
    
    if not prods:
        await callback.message.edit_text("❌ Bu bo'limda hozircha mahsulotlar mavjud emas.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]]))
        return

    await callback.message.edit_text(f"📦 Kerakli miqdorni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("buy_"))
async def ask_player_id(callback: types.CallbackQuery, state: FSMContext):
    _, game, product, price = callback.data.split("_", 3)
    await state.update_data(game=game, product=product, price=int(price))
    
    prompt_text = (
        f"🔗 Kanal yoki guruh havolasini yuboring (Masalan: @kanal_nomi):"
        if game == "subscribers"
        else f"✍️ O'yindagi ID raqamingizni (yoki Telegram username'ingizni) kiriting:"
    )
    
    await callback.message.edit_text(
        f"📦 Tanlangan mahsulot: <b>{product}</b>\n"
        f"💰 Narxi: <b>{price} so'm</b>\n\n"
        f"{prompt_text}"
    )
    await state.set_state(BuyState.waiting_for_input)

@dp.message(BuyState.waiting_for_input)
async def process_purchase(message: types.Message, state: FSMContext):
    player_id = message.text
    data = await state.get_data()
    game = data.get("game")
    product = data.get("product")
    price = data.get("price")
    
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    
    if balance < price:
        await message.answer("❌ Hisobingizda mablag' yetarli emas! Iltimos, balansingizni to'ldiring.", reply_markup=main_menu())
        await state.clear()
        return
    
    update_balance(user_id, -price)
    success = send_auto_donate(game, player_id, product)
    
    if success:
        save_order(user_id, game, product, player_id, "Success")
        await message.answer(
            f"🎉 **Buyurtma muvaffaqiyatli bajarildi!**\n\n"
            f"📦 Xizmat: {game.upper()}\n"
            f"🏷 Mahsulot: {product}\n"
            f"📍 Manzil/ID: `{player_id}`\n"
            f"⚡️ Status: **Avtomatik bajarildi ✅**",
            reply_markup=main_menu()
        )
    else:
        update_balance(user_id, price)
        await message.answer("❌ Xatolik yuz berdi. Mablag'ingiz balansingizga qaytarildi.", reply_markup=main_menu())
        
    await state.clear()

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text("Asosiy menyu:", reply_markup=main_menu())

@dp.callback_query(F.data == "topup")
async def topup_balance(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💳 Balansni to'ldirish uchun to'lov tizimini tanlang (Click / Payme / Uzum):\n\n"
        "*(Admin orqali balans qo'shish imkoniyati ham mavjud)*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
        ])
    )

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    print("Bot barcha funksiyalar bilan ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
