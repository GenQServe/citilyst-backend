from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer, BadTimeSignature, SignatureExpired
import cuid
from passlib.context import CryptContext
from pydantic import EmailStr

from helpers.jwt import JwtHelper
from helpers.config import settings


def _handle_api_response(self, response):
    """
    Helper method to handle API response and raise HTTPException on errors.
    """
    if response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized, please create a new session",
        )
    elif response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Data not found",
        )
    elif response.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail="Bad Request, please check your input",
        )
    elif response.status_code == 500:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error, please try again later",
        )
    elif not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail="Unexpected error occurred",
        )


def generate_cuid():
    return cuid.cuid()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


token_algo = URLSafeTimedSerializer(
    settings.JWT_SECRET, salt="Email_Verification_&_Forgot_password"
)


def create_verification_token(email: EmailStr) -> str:
    """
    Generate a verification token for email confirmation.
    """
    _token = token_algo.dumps(email, salt="Email_Verification_&_Forgot_password")
    return _token


def verify_verification_token(token: str):
    try:
        email = token_algo.loads(token, max_age=1800)
    except SignatureExpired:
        return None
    except BadTimeSignature:
        return None
    return {"email": email, "check": True}
