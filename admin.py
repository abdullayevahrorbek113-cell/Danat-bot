from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
import sqlite3
from database import add_product, update_product_price, update_balance

admin_router = Router()

class AdminState(StatesGroup):
    waiting_for_bal_user = State()
    waiting_for_bal_amount = State()
    waiting_for_prod_game = State()
    waiting_for_prod_name = State()
    waiting_for_prod_price = State()
    waiting_for_new_price = State()

@admin_router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_panel(message: types.Message):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0]
    conn.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Foydalanuvchiga balans berish", callback_data="adm_balance")],
        [InlineKeyboardButton(text="➕ Yangi o'yin/mahsulot qo'shish", callback_data="adm_add_prod")],
        [InlineKeyboardButton(text="✏️ Narxini o'zgartirish", callback_data="adm_edit_price")],
        [InlineKeyboardButton(text="📢 Xabar yuborish (Broadcast)", callback_data="adm_broadcast")]
    ])
    
    await message.answer(
        f"👑 **Admin Boshqaruv Paneli**\n\n"
        f"👥 Jami foydalanuvchilar: {user_count} ta\n"
        f"📦 Jami buyurtmalar: {order_count} ta",
        reply_markup=kb
    )

# Balans berish
@admin_router.callback_query(F.data == "adm_balance", F.from_user.id.in_(ADMIN_IDS))
async def adm_balance_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Foydalanuvchining **Telegram ID** raqamini kiriting:")
    await state.set_state(AdminState.waiting_for_bal_user)

@admin_router.message(AdminState.waiting_for_bal_user, F.from_user.id.in_(ADMIN_IDS))
async def adm_balance_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(target_user=user_id)
        await message.answer("💵 Qo'shiladigan summani kiriting (so'mda, masalan: 50000):")
        await state.set_state(AdminState.waiting_for_bal_amount)
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Faqat raqam kiriting:")

@admin_router.message(AdminState.waiting_for_bal_amount, F.from_user.id.in_(ADMIN_IDS))
async def adm_balance_finish(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        data = await state.get_data()
        target_user = data.get("target_user")
        
        update_balance(target_user, amount)
        await message.answer(f"✅ Foydalanuvchiga {amount} so'm muvaffaqiyatli qo'shildi!")
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")
    await state.clear()

# Narxni o'zgartirish
@admin_router.callback_query(F.data == "adm_edit_price", F.from_user.id.in_(ADMIN_IDS))
async def adm_edit_price_menu(callback: types.CallbackQuery):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, game, product_name, price FROM products")
    products = cursor.fetchall()
    conn.close()
    
    kb = []
    for p_id, game, name, price in products:
        kb.append([InlineKeyboardButton(text=f"{game.upper()} | {name} ({price} so'm)", callback_data=f"setprc_{p_id}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])
    
    await callback.message.edit_text("✏️ Narxini o'zgartirmoqchi bo'lgan mahsulotni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@admin_router.callback_query(F.data.startswith("setprc_"), F.from_user.id.in_(ADMIN_IDS))
async def adm_set_price(callback: types.CallbackQuery, state: FSMContext):
    p_id = callback.data.split("_")[1]
    await state.update_data(edit_p_id=p_id)
    await callback.message.edit_text("✍️ Yangi narxni kiriting (faqat raqam):")
    await state.set_state(AdminState.waiting_for_new_price)

@admin_router.message(AdminState.waiting_for_new_price, F.from_user.id.in_(ADMIN_IDS))
async def adm_save_new_price(message: types.Message, state: FSMContext):
    try:
        new_price = int(message.text)
        data = await state.get_data()
        p_id = data.get("edit_p_id")
        update_product_price(p_id, new_price)
        await message.answer("✅ Mahsulot narxi muvaffaqiyatli yangilandi!")
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")
    await state.clear()

# Yangi mahsulot qo'shish
@admin_router.callback_query(F.data == "adm_add_prod", F.from_user.id.in_(ADMIN_IDS))
async def adm_add_prod_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🎮 O'yin yoki xizmat turini kiriting (masalan: `pubg`, `ff`, `telegram`, `subscribers`):")
    await state.set_state(AdminState.waiting_for_prod_game)

@admin_router.message(AdminState.waiting_for_prod_game, F.from_user.id.in_(ADMIN_IDS))
async def adm_add_prod_game(message: types.Message, state: FSMContext):
    await state.update_data(prod_game=message.text.lower().strip())
    await message.answer("📦 Mahsulot nomini kiriting (masalan: `120 UC` yoki `200 ta Obunachi`):")
    await state.set_state(AdminState.waiting_for_prod_name)

@admin_router.message(AdminState.waiting_for_prod_name, F.from_user.id.in_(ADMIN_IDS))
async def adm_add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(prod_name=message.text.strip())
    await message.answer("💰 Narxini kiriting (so'mda, masalan: 15000):")
    await state.set_state(AdminState.waiting_for_prod_price)

@admin_router.message(AdminState.waiting_for_prod_price, F.from_user.id.in_(ADMIN_IDS))
async def adm_add_prod_finish(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        data = await state.get_data()
        game = data.get("prod_game")
        name = data.get("prod_name")
        
        add_product(game, name, price)
        await message.answer(f"✅ Yangi mahsulot ({name}) muvaffaqiyatli qo'shildi!")
    except ValueError:
        await message.answer("❌ Narx faqat raqamlardan iborat bo'lishi kerak!")
    await state.clear()

@admin_router.callback_query(F.data == "adm_back", F.from_user.id.in_(ADMIN_IDS))
async def adm_back_handler(callback: types.CallbackQuery):
    await admin_panel(callback.message)
