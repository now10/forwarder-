import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import structlog
from app.config import settings

def setup_monitoring():
    """Setup free monitoring tools"""
    
    # Sentry (Error Tracking - free tier available)
    if settings.DEBUG == False and not settings.RENDER:
        sentry_sdk.init(
            dsn="YOUR_SENTRY_DSN",  # Get from sentry.io
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
    
    # Structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )
    
    # Health check logging
    import logging
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    
    logger = structlog.get_logger()
    logger.info("Monitoring setup complete")