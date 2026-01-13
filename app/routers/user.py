from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, get_current_superuser

router = APIRouter()
logger = structlog.get_logger()


@router.get("/stats", response_model=schemas.StatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Get user statistics.
    """
    # Get message stats
    message_stats = await crud.crud_message_log.get_user_stats(db, current_user.id)
    
    # Get rule stats
    rules = await crud.crud_forwarding_rule.get_user_rules(db, current_user.id)
    active_rules = [r for r in rules if r.is_active]
    
    # Get total messages forwarded
    result = await db.execute(
        select(func.sum(TelegramAccount.total_messages_forwarded))
        .where(TelegramAccount.user_id == current_user.id)
    )
    total_messages_forwarded = result.scalar() or 0
    
    return {
        "total_messages_forwarded": total_messages_forwarded,
        "total_rules": len(rules),
        "active_rules": len(active_rules),
        **message_stats
    }


@router.get("/telegram-accounts", response_model=List[schemas.TelegramAccountResponse])
async def get_telegram_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Get user's Telegram accounts.
    """
    accounts = await crud.crud_telegram_account.get_by_user(db, current_user.id)
    return accounts


@router.get("/chats", response_model=List[schemas.TelegramChatResponse])
async def get_chats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """
    Get user's Telegram chats.
    """
    chats = await crud.crud_telegram_chat.get_user_chats(db, current_user.id)
    return chats


# Admin endpoints (for superusers)
@router.get("/admin/users", response_model=List[schemas.UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_superuser)
) -> Any:
    """
    Retrieve users (admin only).
    """
    result = await db.execute(
        select(models.User)
        .offset(skip)
        .limit(limit)
        .order_by(models.User.created_at.desc())
    )
    users = result.scalars().all()
    return users


@router.get("/admin/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
) -> Any:
    """
    Get admin statistics.
    """
    # Total users
    result = await db.execute(select(func.count(models.User.id)))
    total_users = result.scalar()
    
    # Active users (logged in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(func.count(models.User.id))
        .where(models.User.last_login >= thirty_days_ago)
    )
    active_users = result.scalar()
    
    # Total messages forwarded
    result = await db.execute(
        select(func.sum(models.TelegramAccount.total_messages_forwarded))
    )
    total_messages = result.scalar() or 0
    
    # Revenue stats (simplified)
    result = await db.execute(
        select(
            models.User.subscription_tier,
            func.count(models.User.id).label("count")
        )
        .group_by(models.User.subscription_tier)
    )
    subscription_dist = result.all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_messages_forwarded": total_messages,
        "subscription_distribution": {
            tier: count for tier, count in subscription_dist
        }
    }