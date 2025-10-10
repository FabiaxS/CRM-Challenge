from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from enum import Enum

class LeadStatus(str, Enum):
    new = "new"
    qualified = "qualified"
    lost = "lost"

# Create Schemas
class ContactEmailCreate(BaseModel):
    value: EmailStr
    is_primary: Optional[bool] = False

class ContactCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    emails: Optional[List[ContactEmailCreate]] = None

class LeadCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    status: Optional[LeadStatus] = LeadStatus.new
    primary_contact: Optional[ContactCreate] = None

# Read Schemas
class ContactEmailRead(BaseModel):
    id: int
    value: EmailStr
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)

class ContactRead(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    emails: List[ContactEmailRead] = []

    model_config = ConfigDict(from_attributes=True)

class LeadRead(BaseModel):
    id: int
    name: str
    domain: Optional[str]
    status: LeadStatus
    created_at: datetime
    primary_contact: Optional[ContactRead] = None

    model_config = ConfigDict(from_attributes=True)

class LeadsList(BaseModel):
    items: List[LeadRead]
    total: int
