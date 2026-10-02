from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.bot.keyboards.appointment_keyboards import get_main_keyboard

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        f"🏥 Klinika qabuliga yozilish botiga xush kelibsiz.\n"
        f"Iltimos, quyidagi menyudan kerakli bo'limni tanlang:"
    )
    # Bemorga asosiy menyu tugmalarini chiqaramiz
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")
