from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from supabase_auth.errors import AuthApiError

from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=150)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class AuthSessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int | None
    token_type: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest) -> dict[str, str]:
    """Create a Supabase Auth user and its linked public profile."""
    try:
        response = get_supabase_client().auth.admin.create_user(
            {
                "email": str(payload.email),
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {"full_name": payload.full_name or ""},
            }
        )
    except AuthApiError as error:
        message = error.message or "Supabase rejected the registration request"
        logger.warning("Supabase registration rejected: %s", message)
        if "already" in message.lower() or "exists" in message.lower():
            raise HTTPException(status_code=409, detail="An account with this email already exists") from error
        raise HTTPException(status_code=400, detail=f"Registration failed: {message}") from error
    except Exception as error:
        logger.exception("Unexpected registration error")
        raise HTTPException(status_code=500, detail="Registration failed. Check the backend terminal for details.") from error

    return {"id": str(response.user.id), "email": response.user.email}


@router.post("/login", response_model=AuthSessionResponse)
def login_user(payload: LoginRequest) -> AuthSessionResponse:
    """Validate credentials and return a Supabase access token."""
    try:
        response = get_supabase_client().auth.sign_in_with_password(
            {"email": str(payload.email), "password": payload.password}
        )
        session = response.session
        if session is None:
            raise ValueError("No session was returned")
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid email or password") from error

    return AuthSessionResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
        token_type=session.token_type,
    )


@router.get("/me")
def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict[str, object]:
    """Return the user represented by a valid Supabase access token."""
    try:
        response = get_supabase_client().auth.get_user(credentials.credentials)
        user = response.user
        if user is None:
            raise ValueError("No authenticated user")
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from error

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.user_metadata.get("full_name", ""),
    }
