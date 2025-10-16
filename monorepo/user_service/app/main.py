from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from . import config
from .auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from .database import Base, engine, get_db
from .models import User
from .schemas import UserCreate, UserRead, Token, UserUpdate
from sqlalchemy.orm import Session


# Create DB tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if config.ALLOW_ORIGIN_REGEX else config.ALLOW_ORIGINS,
    allow_origin_regex=config.ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        is_active=True,
        is_admin=user_in.is_admin or False,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user: Optional[User] = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "is_admin": user.is_admin}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users", response_model=list[UserRead])
def list_users(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return db.query(User).order_by(User.id.desc()).all()


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        # prevent email collision
        existing = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = payload.email
    if payload.is_active is not None:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can change active state")
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Only admin can change admin flag")
        user.is_admin = payload.is_admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None


