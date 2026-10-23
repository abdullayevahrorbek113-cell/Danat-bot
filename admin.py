from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
import sqlite3

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_balance_user = State()
    waiting_for_balance_amount = State()
    waiting_for_new_prod_name = State()
    waiting_for_new_prod_price = State()
    waiting_for_new_price_value = State()

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
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="💰 Foydalanuvchiga balans berish", callback_data="adm_add_balance")],
        [InlineKeyboardButton(text="➕ Yangi mahsulot/o'yin qo'shish", callback_data="adm_add_prod")],
        [InlineKeyboardButton(text="✏️ Narxlarni o'zgartirish", callback_data="adm_edit_price")]
    ])
    
    await message.answer(
        f"👑 **Admin Boshqaruv Paneli**\n\n"
        f"👥 Jami foydalanuvchilar: {user_count} ta\n"
        f"📦 Jami buyurtmalar: {order_count} ta",
        reply_markup=kb
    )

# Narxni o'zgartirish bo'limi
@admin_router.callback_query(F.data == "adm_edit_price", F.from_user.id.in_(ADMIN_IDS))
async def edit_price_menu(callback: types.CallbackQuery):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, game, product_name, price FROM products")
    products = cursor.fetchall()
    conn.close()
    
    kb = []
    for p_id, game, name, price in products:
        kb.append([InlineKeyboardButton(text=f"{game.upper()} | {name} — {price} so'm", callback_data=f"setprice_{p_id}")])
    kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])
    
    await callback.message.edit_text("✏️ Narxini o'zgartirmoqchi bo'lgan mahsulotni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@admin_router.callback_query(F.data.startswith("setprice_"), F.from_user.id.in_(ADMIN_IDS))
async def set_new_price(callback: types.CallbackQuery, state: FSMContext):
    p_id = callback.data.split("_")[1]
    await state.update_data(edit_p_id=p_id)
    await callback.message.edit_text("✍️ Ushbu mahsulot uchun **yangi narelni** (faqat raqamlarda, masalan: 12000) kiriting:")
    await state.set_state(AdminStates.waiting_for_new_price_value)

@admin_router.message(AdminStates.waiting_for_new_price_value, F.from_user.id.in_(ADMIN_IDS))
async def save_new_price(message: types.Message, state: FSMContext):
    try:
        new_price = int(message.text)
        data = await state.get_data()
        p_id = data.get("edit_p_id")
        
        sqlite3.connect("bot_database.db").cursor().execute("UPDATE products SET price = ? WHERE id = ?", (new_price, p_id))
        # commit qilish uchun:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, p_id))
        conn.commit()
        conn.close()
        
        await message.answer("✅ Mahsulot narxi muvaffaqiyatli yangilandi!")
    except ValueError:
        await message.answer("❌ Iltimos, faqat raqam kiriting!")
    await state.clear()

@admin_router.callback_query(F.data == "adm_back", F.from_user.id.in_(ADMIN_IDS))
async def adm_back(callback: types.CallbackQuery):
    await admin_panel(callback.message)
