from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, RefreshTokenRequest, UserResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=ResponseEnvelope[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register_user(db=db, email=request.email, password=request.password, full_name=request.full_name, phone=request.phone)
        await db.commit()
        await db.refresh(user)
        return ResponseEnvelope(data=UserResponse.model_validate(user), message="User registered successfully")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "REGISTRATION_FAILED", "message": str(e)})

@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.authenticate_user(db, request.email, request.password)
        access_token, refresh_token = await AuthService.create_tokens(db, user)
        await db.commit()
        return ResponseEnvelope(data=TokenResponse(access_token=access_token, expires_in=900, refresh_token=refresh_token), message="Login successful")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "AUTH_FAILED", "message": str(e)})

@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        new_access_token, user = await AuthService.refresh_access_token(db, request.refresh_token)
        return ResponseEnvelope(data=TokenResponse(access_token=new_access_token, expires_in=900, refresh_token=request.refresh_token))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "INVALID_REFRESH_TOKEN", "message": str(e)})

@router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    return ResponseEnvelope(data=UserResponse.model_validate(user))
