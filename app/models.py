from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, 
    ForeignKey, Text, JSON, BigInteger, DECIMAL, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    phone = Column(String(50))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255))
    verification_expires = Column(DateTime)
    
    # Subscription
    subscription_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='inactive')
    subscription_id = Column(String(255))
    current_period_end = Column(DateTime)
    
    # Limits
    max_sources = Column(Integer, default=1)
    max_destinations = Column(Integer, default=1)
    max_keywords = Column(Integer, default=5)
    monthly_message_limit = Column(Integer, default=1000)
    messages_used_this_month = Column(Integer, default=0)
    
    # Security
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    telegram_accounts = relationship("TelegramAccount", back_populates="user", cascade="all, delete-orphan")
    forwarding_rules = relationship("ForwardingRule", back_populates="user", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="owner")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    avatar_url = Column(Text)
    country = Column(String(100))
    industry = Column(String(100))
    use_case = Column(Text)
    telegram_username = Column(String(255))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="profile")


class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Telegram credentials (will be encrypted in application layer)
    api_id = Column(String(100), nullable=False)
    api_hash = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    session_data = Column(Text)  # Encrypted session
    
    # Telegram user info
    telegram_user_id = Column(BigInteger)
    telegram_username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    
    # Stats
    total_messages_forwarded = Column(Integer, default=0)
    last_forwarded_at = Column(DateTime)
    
    # Security
    connection_token = Column(String(255), unique=True)
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="telegram_accounts")
    chats = relationship("TelegramChat", back_populates="telegram_account", cascade="all, delete-orphan")
    forwarding_rules = relationship("ForwardingRule", back_populates="telegram_account", cascade="all, delete-orphan")


class TelegramChat(Base):
    __tablename__ = "telegram_chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_account_id = Column(UUID(as_uuid=True), ForeignKey("telegram_accounts.id", ondelete="CASCADE"))
    
    # Telegram data
    chat_id = Column(BigInteger, nullable=False)
    chat_type = Column(String(50), nullable=False)
    chat_title = Column(String(255))
    chat_username = Column(String(255))
    invite_link = Column(Text)
    
    # Access info
    is_accessible = Column(Boolean, default=True)
    last_accessed = Column(DateTime)
    permissions_json = Column(JSON)
    
    # Business categorization
    is_source = Column(Boolean, default=False)
    is_destination = Column(Boolean, default=False)
    auto_discovered = Column(Boolean, default=True)
    
    # Statistics
    total_messages = Column(Integer, default=0)
    last_message_id = Column(BigInteger, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    telegram_account = relationship("TelegramAccount", back_populates="chats")
    source_rules = relationship("ForwardingRule", foreign_keys="[ForwardingRule.source_chat_id]", back_populates="source_chat")
    destination_rules = relationship("ForwardingRule", foreign_keys="[ForwardingRule.destination_chat_id]", back_populates="destination_chat")


class ForwardingRule(Base):
    __tablename__ = "forwarding_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    telegram_account_id = Column(UUID(as_uuid=True), ForeignKey("telegram_accounts.id", ondelete="CASCADE"))
    
    # Source and destination
    source_chat_id = Column(UUID(as_uuid=True), ForeignKey("telegram_chats.id", ondelete="CASCADE"))
    destination_chat_id = Column(UUID(as_uuid=True), ForeignKey("telegram_chats.id", ondelete="CASCADE"))
    
    # Rule configuration
    rule_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    forward_mode = Column(String(50), default='all')
    
    # Filter conditions
    keywords = Column(ARRAY(Text))
    regex_patterns = Column(ARRAY(Text))
    filter_logic = Column(String(20), default='any')
    case_sensitive = Column(Boolean, default=False)
    
    # Advanced filters
    min_message_length = Column(Integer)
    max_message_length = Column(Integer)
    allowed_senders = Column(ARRAY(Text))
    excluded_senders = Column(ARRAY(Text))
    
    # Time-based rules
    timezone = Column(String(50))
    active_hours = Column(JSON)
    enable_scheduling = Column(Boolean, default=False)
    
    # Forwarding behavior
    include_media = Column(Boolean, default=True)
    include_links = Column(Boolean, default=True)
    include_forwarded = Column(Boolean, default=True)
    add_prefix = Column(Text)
    add_suffix = Column(Text)
    
    # Rate limiting
    max_forwards_per_hour = Column(Integer, default=100)
    min_interval_seconds = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="forwarding_rules")
    telegram_account = relationship("TelegramAccount", back_populates="forwarding_rules")
    source_chat = relationship("TelegramChat", foreign_keys=[source_chat_id], back_populates="source_rules")
    destination_chat = relationship("TelegramChat", foreign_keys=[destination_chat_id], back_populates="destination_rules")
    message_logs = relationship("MessageLog", back_populates="rule", cascade="all, delete-orphan")


class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("forwarding_rules.id", ondelete="SET NULL"))
    telegram_account_id = Column(UUID(as_uuid=True), ForeignKey("telegram_accounts.id", ondelete="CASCADE"))
    
    # Message info
    source_chat_id = Column(BigInteger)
    destination_chat_id = Column(BigInteger)
    telegram_message_id = Column(BigInteger)
    forwarded_message_id = Column(BigInteger)
    
    # Content
    message_text = Column(Text)
    sender_username = Column(String(255))
    sender_id = Column(BigInteger)
    has_media = Column(Boolean, default=False)
    media_type = Column(String(50))
    
    # Processing info
    matched_keywords = Column(ARRAY(Text))
    matched_patterns = Column(ARRAY(Text))
    processing_time_ms = Column(Integer)
    
    # Status
    status = Column(String(50), default='success')
    error_message = Column(Text)
    
    forwarded_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rule = relationship("ForwardingRule", back_populates="message_logs")
    telegram_account = relationship("TelegramAccount")


# (Additional models for Team, ApiKey, Notification, etc. following similar pattern)
# Due to character limit, I'll show the most critical ones above