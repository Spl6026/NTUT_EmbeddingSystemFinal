from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class ParkingViolationLog(Base):
    __tablename__ = "parking_violation_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    image_path = Column(String)
    is_violation = Column(Boolean, default=False)
    car_detected = Column(Boolean, default=False)
    status = Column(String)