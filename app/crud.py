from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timedelta

from app.models import (
    User, UserProfile, TelegramAccount, TelegramChat, 
    ForwardingRule, MessageLog, ApiKey
)
from app.schemas import (
    UserCreate, UserUpdate, TelegramAccountCreate,
    ForwardingRuleCreate, ForwardingRuleUpdate
)
from app.core.security import security, encryption
import structlog

logger = structlog.get_logger()


class CRUDUser:
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        # Check if user already exists
        existing_user = await self.get_by_email(db, obj_in.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user
        db_obj = User(
            email=obj_in.email,
            password_hash=security.get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            company_name=obj_in.company_name,
            phone=obj_in.phone,
            verification_token=security.create_verification_token(obj_in.email),
            verification_expires=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Create user profile
        profile = UserProfile(user_id=db_obj.id)
        db.add(profile)
        await db.commit()
        
        logger.info("User created", user_id=str(db_obj.id), email=obj_in.email)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: User, obj_in: UserUpdate
    ) -> User:
        update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def verify_email(self, db: AsyncSession, token: str) -> Optional[User]:
        email = security.verify_verification_token(token)
        if not email:
            return None
        
        user = await self.get_by_email(db, email)
        if not user:
            return None
        
        user.is_verified = True
        user.verification_token = None
        user.verification_expires = None
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("Email verified", user_id=str(user.id), email=email)
        return user

    async def update_password(
        self, db: AsyncSession, user_id: uuid.UUID, new_password: str
    ) -> Optional[User]:
        user = await self.get(db, user_id)
        if not user:
            return None
        
        user.password_hash = security.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("Password updated", user_id=str(user_id))
        return user

    async def increment_message_count(
        self, db: AsyncSession, user_id: uuid.UUID, count: int = 1
    ) -> None:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(messages_used_this_month=User.messages_used_this_month + count)
        )
        await db.commit()


class CRUDTelegramAccount:
    async def get_by_user(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[TelegramAccount]:
        result = await db.execute(
            select(TelegramAccount)
            .where(TelegramAccount.user_id == user_id)
            .order_by(TelegramAccount.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, account_id: uuid.UUID
    ) -> Optional[TelegramAccount]:
        result = await db.execute(
            select(TelegramAccount)
            .where(TelegramAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, db: AsyncSession, user_id: uuid.UUID, obj_in: TelegramAccountCreate
    ) -> TelegramAccount:
        # Check if account already exists for this user
        result = await db.execute(
            select(TelegramAccount)
            .where(
                and_(
                    TelegramAccount.user_id == user_id,
                    TelegramAccount.phone_number == obj_in.phone_number
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError("Telegram account already connected")
        
        # Encrypt sensitive data
        encrypted_creds = encryption.encrypt_telegram_credentials(
            obj_in.api_id, obj_in.api_hash, obj_in.phone_number
        )
        
        # Generate connection token
        import secrets
        connection_token = secrets.token_urlsafe(32)
        
        db_obj = TelegramAccount(
            user_id=user_id,
            api_id=encrypted_creds["api_id"],
            api_hash=encrypted_creds["api_hash"],
            phone_number=encrypted_creds["phone_number"],
            connection_token=connection_token,
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info("Telegram account created", 
                   account_id=str(db_obj.id), 
                   user_id=str(user_id))
        return db_obj

    async def update_connection_status(
        self, db: AsyncSession, account_id: uuid.UUID, 
        is_connected: bool, telegram_user_info: Optional[Dict] = None
    ) -> Optional[TelegramAccount]:
        account = await self.get_by_id(db, account_id)
        if not account:
            return None
        
        account.is_connected = is_connected
        account.last_sync = datetime.utcnow()
        
        if telegram_user_info:
            account.telegram_user_id = telegram_user_info.get("id")
            account.telegram_username = telegram_user_info.get("username")
            account.first_name = telegram_user_info.get("first_name")
            account.last_name = telegram_user_info.get("last_name")
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
        
        logger.info("Telegram account connection updated",
                   account_id=str(account_id),
                   is_connected=is_connected)
        return account

    async def delete(self, db: AsyncSession, account_id: uuid.UUID) -> bool:
        result = await db.execute(
            delete(TelegramAccount)
            .where(TelegramAccount.id == account_id)
            .returning(TelegramAccount.id)
        )
        deleted_id = result.scalar_one_or_none()
        await db.commit()
        
        if deleted_id:
            logger.info("Telegram account deleted", account_id=str(account_id))
            return True
        return False


class CRUDTelegramChat:
    async def get_user_chats(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[TelegramChat]:
        result = await db.execute(
            select(TelegramChat)
            .join(TelegramAccount)
            .where(TelegramAccount.user_id == user_id)
            .order_by(TelegramChat.chat_type, TelegramChat.chat_title)
        )
        return result.scalars().all()

    async def bulk_create_or_update(
        self, db: AsyncSession, account_id: uuid.UUID, chats_data: List[Dict]
    ) -> List[TelegramChat]:
        existing_chats = {}
        
        # Get existing chats for this account
        result = await db.execute(
            select(TelegramChat)
            .where(TelegramChat.telegram_account_id == account_id)
        )
        for chat in result.scalars():
            existing_chats[chat.chat_id] = chat
        
        updated_chats = []
        for chat_data in chats_data:
            chat_id = chat_data["id"]
            
            if chat_id in existing_chats:
                # Update existing chat
                chat = existing_chats[chat_id]
                chat.chat_title = chat_data.get("title")
                chat.chat_username = chat_data.get("username")
                chat.chat_type = chat_data.get("type")
                chat.last_accessed = datetime.utcnow()
                chat.is_accessible = True
            else:
                # Create new chat
                chat = TelegramChat(
                    telegram_account_id=account_id,
                    chat_id=chat_id,
                    chat_title=chat_data.get("title"),
                    chat_username=chat_data.get("username"),
                    chat_type=chat_data.get("type"),
                    last_accessed=datetime.utcnow()
                )
                db.add(chat)
            
            updated_chats.append(chat)
        
        await db.commit()
        
        # Refresh all updated chats
        for chat in updated_chats:
            await db.refresh(chat)
        
        logger.info("Chats synced", 
                   account_id=str(account_id), 
                   total_chats=len(updated_chats))
        return updated_chats


class CRUDForwardingRule:
    async def get_user_rules(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[ForwardingRule]:
        result = await db.execute(
            select(ForwardingRule)
            .where(ForwardingRule.user_id == user_id)
            .options(
                selectinload(ForwardingRule.source_chat),
                selectinload(ForwardingRule.destination_chat)
            )
            .order_by(ForwardingRule.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_rules(
        self, db: AsyncSession
    ) -> List[ForwardingRule]:
        result = await db.execute(
            select(ForwardingRule)
            .where(ForwardingRule.is_active == True)
            .options(
                selectinload(ForwardingRule.source_chat),
                selectinload(ForwardingRule.destination_chat),
                selectinload(ForwardingRule.telegram_account)
            )
        )
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, user_id: uuid.UUID, obj_in: ForwardingRuleCreate
    ) -> ForwardingRule:
        # Check if user has reached rule limit
        from app.crud import crud_user
        user = await crud_user.get(db, user_id)
        
        # Count user's existing rules
        result = await db.execute(
            select(func.count(ForwardingRule.id))
            .where(ForwardingRule.user_id == user_id)
        )
        rule_count = result.scalar()
        
        # Check limits based on subscription tier
        if user.subscription_tier == "free" and rule_count >= 3:
            raise ValueError("Free tier limited to 3 forwarding rules")
        elif user.subscription_tier == "pro" and rule_count >= 20:
            raise ValueError("Pro tier limited to 20 forwarding rules")
        
        db_obj = ForwardingRule(
            user_id=user_id,
            telegram_account_id=obj_in.telegram_account_id,
            source_chat_id=obj_in.source_chat_id,
            destination_chat_id=obj_in.destination_chat_id,
            rule_name=obj_in.rule_name,
            is_active=obj_in.is_active,
            forward_mode=obj_in.forward_mode,
            keywords=obj_in.keywords,
            regex_patterns=obj_in.regex_patterns,
            filter_logic=obj_in.filter_logic,
            case_sensitive=obj_in.case_sensitive,
            min_message_length=obj_in.min_message_length,
            max_message_length=obj_in.max_message_length,
            allowed_senders=obj_in.allowed_senders,
            excluded_senders=obj_in.excluded_senders,
            timezone=obj_in.timezone,
            active_hours=obj_in.active_hours,
            enable_scheduling=obj_in.enable_scheduling,
            include_media=obj_in.include_media,
            include_links=obj_in.include_links,
            include_forwarded=obj_in.include_forwarded,
            add_prefix=obj_in.add_prefix,
            add_suffix=obj_in.add_suffix,
            max_forwards_per_hour=obj_in.max_forwards_per_hour,
            min_interval_seconds=obj_in.min_interval_seconds
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        logger.info("Forwarding rule created", 
                   rule_id=str(db_obj.id), 
                   user_id=str(user_id))
        return db_obj

    async def update(
        self, db: AsyncSession, rule_id: uuid.UUID, obj_in: ForwardingRuleUpdate
    ) -> Optional[ForwardingRule]:
        rule = await self.get_by_id(db, rule_id)
        if not rule:
            return None
        
        update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            setattr(rule, field, update_data[field])
        
        rule.updated_at = datetime.utcnow()
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info("Forwarding rule updated", rule_id=str(rule_id))
        return rule

    async def get_by_id(
        self, db: AsyncSession, rule_id: uuid.UUID
    ) -> Optional[ForwardingRule]:
        result = await db.execute(
            select(ForwardingRule)
            .where(ForwardingRule.id == rule_id)
            .options(
                selectinload(ForwardingRule.source_chat),
                selectinload(ForwardingRule.destination_chat),
                selectinload(ForwardingRule.telegram_account)
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, rule_id: uuid.UUID) -> bool:
        result = await db.execute(
            delete(ForwardingRule)
            .where(ForwardingRule.id == rule_id)
            .returning(ForwardingRule.id)
        )
        deleted_id = result.scalar_one_or_none()
        await db.commit()
        
        if deleted_id:
            logger.info("Forwarding rule deleted", rule_id=str(rule_id))
            return True
        return False


class CRUDMessageLog:
    async def create(
        self, db: AsyncSession, log_data: Dict[str, Any]
    ) -> MessageLog:
        db_obj = MessageLog(**log_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_rule_logs(
        self, db: AsyncSession, rule_id: uuid.UUID, limit: int = 100
    ) -> List[MessageLog]:
        result = await db.execute(
            select(MessageLog)
            .where(MessageLog.rule_id == rule_id)
            .order_by(MessageLog.forwarded_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_user_stats(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        # Get today's date at midnight
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Messages today
        result = await db.execute(
            select(func.count(MessageLog.id))
            .join(ForwardingRule)
            .where(
                and_(
                    ForwardingRule.user_id == user_id,
                    MessageLog.forwarded_at >= today
                )
            )
        )
        messages_today = result.scalar() or 0
        
        # Messages this month
        first_day_of_month = today.replace(day=1)
        result = await db.execute(
            select(func.count(MessageLog.id))
            .join(ForwardingRule)
            .where(
                and_(
                    ForwardingRule.user_id == user_id,
                    MessageLog.forwarded_at >= first_day_of_month
                )
            )
        )
        messages_this_month = result.scalar() or 0
        
        # Success rate
        result = await db.execute(
            select(
                func.count(MessageLog.id).label("total"),
                func.count(case((MessageLog.status == 'success', 1))).label("success")
            )
            .join(ForwardingRule)
            .where(ForwardingRule.user_id == user_id)
        )
        row = result.first()
        success_rate = (row.success / row.total * 100) if row and row.total > 0 else 100
        
        # Average processing time
        result = await db.execute(
            select(func.avg(MessageLog.processing_time_ms))
            .join(ForwardingRule)
            .where(
                and_(
                    ForwardingRule.user_id == user_id,
                    MessageLog.processing_time_ms.isnot(None)
                )
            )
        )
        avg_processing_time = result.scalar() or 0
        
        return {
            "messages_today": messages_today,
            "messages_this_month": messages_this_month,
            "success_rate": round(success_rate, 2),
            "average_processing_time_ms": round(avg_processing_time, 2)
        }


class CRUDApiKey:
    async def validate_api_key(
        self, db: AsyncSession, api_key: str
    ) -> Optional[uuid.UUID]:
        result = await db.execute(
            select(ApiKey)
            .where(
                and_(
                    ApiKey.api_key == api_key,
                    ApiKey.is_active == True,
                    or_(
                        ApiKey.expires_at.is_(None),
                        ApiKey.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        api_key_obj = result.scalar_one_or_none()
        
        if api_key_obj:
            # Update last used
            api_key_obj.last_used = datetime.utcnow()
            api_key_obj.usage_count += 1
            db.add(api_key_obj)
            await db.commit()
            
            return api_key_obj.user_id
        
        return None


# Create instances
crud_user = CRUDUser()
crud_telegram_account = CRUDTelegramAccount()
crud_telegram_chat = CRUDTelegramChat()
crud_forwarding_rule = CRUDForwardingRule()
crud_message_log = CRUDMessageLog()
crud_api_key = CRUDApiKey()