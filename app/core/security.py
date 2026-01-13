from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import settings
from cryptography.fernet import Fernet
import base64
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Security:
    @staticmethod
    def create_access_token(
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            subject: str = payload.get("sub")
            if subject is None:
                return None
            return subject
        except jwt.JWTError:
            return None

    @staticmethod
    def create_verification_token(email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"exp": expire, "email": email, "type": "verification"}
        return jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

    @staticmethod
    def verify_verification_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "verification":
                return None
            email: str = payload.get("email")
            return email
        except jwt.JWTError:
            return None

    @staticmethod
    def create_password_reset_token(email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {"exp": expire, "email": email, "type": "reset"}
        return jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "reset":
                return None
            email: str = payload.get("email")
            return email
        except jwt.JWTError:
            return None


class DataEncryption:
    _fernet = None
    
    @classmethod
    def _get_fernet(cls):
        if cls._fernet is None:
            # Derive key from SECRET_KEY
            key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key[:32])
            cls._fernet = Fernet(fernet_key)
        return cls._fernet
    
    @classmethod
    def encrypt_data(cls, data: str) -> str:
        fernet = cls._get_fernet()
        return fernet.encrypt(data.encode()).decode()
    
    @classmethod
    def decrypt_data(cls, encrypted_data: str) -> str:
        fernet = cls._get_fernet()
        return fernet.decrypt(encrypted_data.encode()).decode()
    
    @classmethod
    def encrypt_telegram_credentials(
        cls, 
        api_id: str, 
        api_hash: str, 
        phone_number: str
    ) -> dict:
        return {
            "api_id": cls.encrypt_data(api_id),
            "api_hash": cls.encrypt_data(api_hash),
            "phone_number": cls.encrypt_data(phone_number)
        }
    
    @classmethod
    def decrypt_telegram_credentials(cls, encrypted_data: dict) -> dict:
        return {
            "api_id": cls.decrypt_data(encrypted_data["api_id"]),
            "api_hash": cls.decrypt_data(encrypted_data["api_hash"]),
            "phone_number": cls.decrypt_data(encrypted_data["phone_number"])
        }


security = Security()
encryption = DataEncryption()