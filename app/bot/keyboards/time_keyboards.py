from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class DateSelectCallback(CallbackData, prefix="sel_date"):
    date_str: str


class SlotSelectCallback(CallbackData, prefix="sel_slot"):
    time_str: str


def get_next_days_keyboard(days_count: int = 7) -> InlineKeyboardMarkup:
    """Kelgusi 7 kunlik sanalar tugmalari"""
    builder = InlineKeyboardBuilder()
    today = date.today()

    hafta_kunlari = {0: "Dush", 1: "Sesh", 2: "Chor", 3: "Pay", 4: "Jum", 5: "Shan", 6: "Yak"}

    for i in range(days_count):
        d = today + timedelta(days=i)
        day_name = hafta_kunlari[d.weekday()]
        text = f"{d.strftime('%d.%m')} ({day_name})"
        if i == 0:
            text = f"Bugun ({d.strftime('%d.%m')})"
        elif i == 1:
            text = f"Ertaga ({d.strftime('%d.%m')})"

        builder.button(
            text=text,
            callback_data=DateSelectCallback(date_str=d.isoformat())
        )

    builder.adjust(2)  # Qatoriga 2 tadan sana
    return builder.as_markup()


def get_slots_keyboard(slots: list) -> InlineKeyboardMarkup:
    """Bo'sh vaqt slotlarini 4 ustun qilib chiqarish"""
    builder = InlineKeyboardBuilder()

    for slot in slots:
        builder.button(
            text=f"🟢 {slot['time']}",
            callback_data=SlotSelectCallback(time_str=slot['time'])
        )

    builder.adjust(4)  # Masalan: [09:00] [09:20] [09:40] [10:00]
    builder.button(text="◀️ Boshqa sana tanlash", callback_data="change_date")
    return builder.as_markup()
