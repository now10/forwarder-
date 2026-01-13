from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID
import re


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class UserInDB(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass


class TelegramAccountBase(BaseModel):
    phone_number: str
    api_id: str
    api_hash: str


class TelegramAccountCreate(TelegramAccountBase):
    verification_code: Optional[str] = None
    password: Optional[str] = None  # 2FA password


class TelegramAccountResponse(BaseModel):
    id: UUID
    phone_number: str
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_connected: bool
    total_messages_forwarded: int
    last_sync: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TelegramChatBase(BaseModel):
    chat_id: int
    chat_type: str
    chat_title: Optional[str] = None
    chat_username: Optional[str] = None


class TelegramChatResponse(TelegramChatBase):
    id: UUID
    is_accessible: bool
    is_source: bool
    is_destination: bool
    total_messages: int
    last_accessed: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForwardingRuleBase(BaseModel):
    rule_name: str
    source_chat_id: UUID
    destination_chat_id: UUID
    is_active: bool = True
    forward_mode: str = "all"
    
    # Filter conditions
    keywords: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None
    filter_logic: str = "any"
    case_sensitive: bool = False
    
    # Advanced filters
    min_message_length: Optional[int] = None
    max_message_length: Optional[int] = None
    allowed_senders: Optional[List[str]] = None
    excluded_senders: Optional[List[str]] = None
    
    # Time-based
    timezone: Optional[str] = None
    active_hours: Optional[Dict[str, Any]] = None
    enable_scheduling: bool = False
    
    # Behavior
    include_media: bool = True
    include_links: bool = True
    include_forwarded: bool = True
    add_prefix: Optional[str] = None
    add_suffix: Optional[str] = None
    
    # Rate limiting
    max_forwards_per_hour: int = 100
    min_interval_seconds: int = 0


class ForwardingRuleCreate(ForwardingRuleBase):
    telegram_account_id: UUID


class ForwardingRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    is_active: Optional[bool] = None
    keywords: Optional[List[str]] = None
    # ... other updatable fields


class ForwardingRuleResponse(ForwardingRuleBase):
    id: UUID
    user_id: UUID
    telegram_account_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageLogResponse(BaseModel):
    id: UUID
    rule_id: Optional[UUID]
    telegram_message_id: int
    forwarded_message_id: Optional[int]
    message_text: Optional[str]
    sender_username: Optional[str]
    status: str
    matched_keywords: Optional[List[str]]
    processing_time_ms: int
    forwarded_at: datetime
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_messages_forwarded: int
    total_rules: int
    active_rules: int
    messages_today: int
    messages_this_month: int
    success_rate: float
    average_processing_time_ms: float


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class NewPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerificationRequest(BaseModel):
    token: str