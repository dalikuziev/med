import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models import Clinic, Doctor, Base

# Baza manzili (o'zingizdagi manzil bilan bir xil ekanini tekshiring)
DATABASE_URL = "sqlite+aiosqlite:///./med_queue.db"

async def seed_data():
    engine = create_async_engine(DATABASE_URL)

    # Jadvallarni yaratish (agar hali ochilmagan bo'lsa)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # 1. Klinikalar yaratish
        clinic1 = Clinic(name="Shifo Med (Chilonzor)", phone="+998712000000", address="Chilonzor tumani, 9-mavze")
        clinic2 = Clinic(name="Akfa Medline (Olmazor)", phone="+998712001111", address="Olmazor tumani, Qamarniso")

        session.add_all([clinic1, clinic2])
        await session.flush()  # Klinikalar ID olishi uchun flush qilamiz

        # 2. Shifokorlarni klinikalarga biriktirib yaratish
        doc1 = Doctor(clinic_id=clinic1.id, full_name="Dr. Alisher Vohidov", specialty="Kardiolog", room_number="101",
                      slot_duration=20)
        doc2 = Doctor(clinic_id=clinic1.id, full_name="Dr. Malika Karimova", specialty="Nevrolog", room_number="102",
                      slot_duration=15)
        doc3 = Doctor(clinic_id=clinic2.id, full_name="Dr. Rustam Umarov", specialty="Xirurg", room_number="205",
                      slot_duration=30)

        session.add_all([doc1, doc2, doc3])
        await session.commit()

    print("✅ Baza muvaffaqiyatli test ma'lumotlari bilan to'ldirildi!")


if __name__ == "__main__":
    asyncio.run(seed_data())
