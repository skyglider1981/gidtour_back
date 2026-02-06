from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, BusinessProfile, CustomerProfile
from app.schemas.user import UserRegister, UserLogin, Token, BusinessUserResponse

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=Token)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    # Проверяем, не занят ли email
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Создаём пользователя
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        user_type=data.user_type,
        full_name=data.full_name,
        phone=data.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Создаём профиль в зависимости от типа
    if data.user_type == "business":
        profile = BusinessProfile(
            user_id=user.id,
            business_name=data.full_name  # Временно используем имя
        )
        db.add(profile)
    else:
        profile = CustomerProfile(user_id=user.id)
        db.add(profile)
    
    db.commit()
    
    # Генерируем токен
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        user_type=user.user_type,
        user_id=user.id
    )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Вход в систему"""
    
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        user_type=user.user_type,
        user_id=user.id
    )


@router.get("/me", response_model=BusinessUserResponse)
async def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(__import__('app.api.deps', fromlist=['get_current_user']).get_current_user)
):
    """Получить данные текущего пользователя"""
    return current_user
