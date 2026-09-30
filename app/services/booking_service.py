from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import Appointment, Doctor, Clinic  # Modelingizga qarab


class BookingService:
    @staticmethod
    async def create_appointment(
            session: AsyncSession,
            clinic_id: int,
            doctor_id: int,
            user_id: int,
            patient_name: str,
            patient_phone: str,
            appt_date: date,
            appt_time: time
    ) -> Appointment:
        """Tranzaksiya ichida navbatni xavfsiz saqlash va navbat raqamini berish"""
        async with session.begin():
            # O'sha kuni ushbu shifokorga nechta navbat bo'lganini sanab, keyingi raqamni beramiz
            stmt = select(func.count(Appointment.id)).where(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appt_date
            )
            count_result = await session.execute(stmt)
            queue_number = (count_result.scalar() or 0) + 1

            appointment = Appointment(
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                user_id=user_id,
                patient_name=patient_name,
                patient_phone=patient_phone,
                appointment_date=appt_date,
                start_time=appt_time,
                status="confirmed",
                queue_number=queue_number
            )
            session.add(appointment)
            await session.flush()
            await session.refresh(appointment)
            return appointment

    @staticmethod
    async def cancel_appointment(session: AsyncSession, appointment_id: int, user_id: int) -> bool:
        """Navbatni bekor qilish"""
        stmt = select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.user_id == user_id
        )
        res = await session.execute(stmt)
        appointment = res.scalar_one_or_none()

        if appointment and appointment.status != "cancelled":
            appointment.status = "cancelled"
            await session.commit()
            return True
        return False
