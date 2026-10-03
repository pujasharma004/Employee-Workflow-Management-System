
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="employee")

    department_id = Column(Integer, ForeignKey("departments.id"))
    is_available = Column(Boolean, default=True)

    requests = relationship(
        "Request",
        back_populates="user",
        foreign_keys="Request.user_id"
    )

    assigned_requests = relationship(
        "Request",
        back_populates="assigned_agent",
        foreign_keys="Request.assigned_agent_id"
    )

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    requests = relationship("Request", back_populates="department")


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String, nullable=False)
    priority = Column(String, default="Medium")
    status = Column(String, default="Open")

    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    assigned_agent_id = Column(Integer, ForeignKey("users.id"))

    user = relationship(
        "User",
        back_populates="requests",
        foreign_keys=[user_id]
    )

    assigned_agent = relationship(
        "User",
        back_populates="assigned_requests",
        foreign_keys=[assigned_agent_id]
    )

    department = relationship(
        "Department",
        back_populates="requests"
    )

    sla_deadline = Column(DateTime, nullable=True)
