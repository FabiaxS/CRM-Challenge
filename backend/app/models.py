from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    ForeignKey,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import enum
from .database import Base

class LeadStatus(str, enum.Enum):
    new = "new"
    qualified = "qualified"
    lost = "lost"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.new, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Optionaler Primärkontakt (FK)
    primary_contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    primary_contact = relationship("Contact", foreign_keys=[primary_contact_id])

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    emails = relationship("ContactEmail", back_populates="contact", cascade="all, delete-orphan")

class ContactEmail(Base):
    __tablename__ = "contact_emails"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    value = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    contact = relationship("Contact", back_populates="emails")

    __table_args__ = (
        # Jede E-Mail darf pro Kontakt nur einmal vorkommen
        # In SQLite wird CASE-INSENSITIVE-Unique im Code geprüft
        UniqueConstraint("contact_id", "value", name="uq_contact_email_contact_value"),
    )
