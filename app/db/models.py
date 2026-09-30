from datetime import date, time, datetime
from sqlalchemy import BigInteger, String, ForeignKey, Date, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="clinic")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="clinic")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String(255))
    specialty: Mapped[str] = mapped_column(String(100))
    room_number: Mapped[str] = mapped_column(String(20), default="101")
    slot_duration: Mapped[int] = mapped_column(default=20)  # daqiqada

    clinic: Mapped["Clinic"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger)  # Telegram user ID
    patient_name: Mapped[str] = mapped_column(String(255))
    patient_phone: Mapped[str] = mapped_column(String(50))
    appointment_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(50), default="confirmed")  # confirmed, cancelled, completed
    queue_number: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    clinic: Mapped["Clinic"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")

    __table_args__ = (
        # Bir shifokorga bitta vaqtga 2 ta aktiv navbat tushishini taqiqlash
        UniqueConstraint("doctor_id", "appointment_date", "start_time", name="uq_doctor_slot"),
    )
