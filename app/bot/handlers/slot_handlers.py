from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from app.bot.keyboards.time_keyboards import SlotSelectCallback
from app.services.slot_service import SlotEngine
slot_router = Router()

@slot_router.callback_query(SlotSelectCallback.filter())
async def on_slot_clicked(
    callback: CallbackQuery,
    callback_data: SlotSelectCallback,
    state: FSMContext,
    slot_engine: SlotEngine
):
    user_data = await state.get_data()
    doctor_id = user_data["selected_doctor_id"]
    target_date = datetime.fromisoformat(user_data["selected_date"]).date()
    chosen_time = callback_data.time_str

    # Redis orqali ushbu vaqtni foydalanuvchiga 2 daqiqaga bron qilamiz
    is_locked = await slot_engine.lock_slot_temporarily(
        doctor_id=doctor_id,
        target_date=target_date,
        slot_time=chosen_time,
        user_id=callback.from_user.id,
        ttl_seconds=120
    )

    if not is_locked:
        await callback.answer(
            "⚠️ Uzr, ushbu vaqtni bir necha soniya oldin boshqa bemor tanladi. Iltimos, boshqa vaqtni tanlang!",
            show_alert=True
        )
        return

    # Vaqt muvaffaqiyatli band qilib turildi, endi tasdiqlash sahifasiga o'tamiz
    await state.update_data(selected_time=chosen_time)
    await callback.message.edit_text(
        f"Siz tanladingiz:\n"
        f"📅 Sana: <b>{target_date}</b>\n"
        f"⏰ Vaqt: <b>{chosen_time}</b>\n\n"
        f"<i>Ushbu vaqt siz uchun 2 daqiqa davomida saqlanadi. Iltimos, qabulni tasdiqlang.</i>",
        # reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
