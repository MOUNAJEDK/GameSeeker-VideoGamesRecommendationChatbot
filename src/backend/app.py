import asyncio
import nest_asyncio
import markdown2
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from langgraph_logic.graph import create_graph
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import re
from models import Base, User, MentionedGame, Thread, PasswordResetToken, RefreshToken, VerificationKey
import secrets
from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

client = Client()

# Setup asyncio for Windows
if asyncio.get_event_loop().is_closed():
    asyncio.set_event_loop(asyncio.ProactorEventLoop())
else:
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./users.db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for JWT. Please add it to .env file.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI app setup
app = FastAPI(
    title="Video Game Recommendation Chatbot",
    version="1.0",
    description="An API server to provide personalized video game recommendations."
)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=int(os.getenv('MAIL_PORT')),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Dependency to get the database session
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Create the graph with the database session factory
graph = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int):
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=30)
    return RefreshToken(user_id=user_id, token=token, expires_at=expires)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(db, username)
    if user is None:
        raise credentials_exception
    return user

async def send_email_async(subject: str, email_to: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)
    verification_key: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must only contain letters, numbers, and underscores')
        return v

    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'\W', v):
            raise ValueError('Password must contain at least one special character')
        return v

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Input(BaseModel):
    input: str
    thread_id: str

class Output(BaseModel):
    output: List[str]

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class UserOut(BaseModel):
    username: str
    email: str

class ThreadResponse(BaseModel):
    thread_id: str

# Routes
@app.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Verify the key
    db_key = await db.execute(select(VerificationKey).filter(VerificationKey.email == user.email, VerificationKey.key == user.verification_key, VerificationKey.expires_at > datetime.utcnow()))
    db_key = db_key.scalar_one_or_none()
    if not db_key:
        raise HTTPException(status_code=400, detail="Invalid or expired verification key")
    
    # Proceed with user registration
    db_user = await get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    
    # Delete the used verification key
    await db.delete(db_key)
    
    await db.commit()
    await db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(new_user.id)
    db.add(refresh_token)
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token.token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.id)
    db.add(refresh_token)
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token.token, "token_type": "bearer"}

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

@app.post("/chat")
async def chat_endpoint(
    input_data: Input,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_input = input_data.input
    thread_id = input_data.thread_id

    # Verify that the thread belongs to the current user
    result = await db.execute(select(Thread).filter(Thread.thread_id == thread_id, Thread.user_id == current_user.id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found or does not belong to the current user")

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    state = {
        "query": user_input,
        "category": "",
        "games": [],
        "details": {},
        "links": [],
        "index": 0,
        "response": "",
        "user_id": current_user.id,
    }

    output = await graph.ainvoke(state, config=config)
    formatted_output = markdown2.markdown(output["response"])
    formatted_output = formatted_output.replace('\n', '<br>')

    return {"output": [formatted_output]}

@app.post("/new-chat", response_model=ThreadResponse)
async def new_chat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Generate a new unique thread_id for the user
    new_thread_id = f"user_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    # Create a new Thread instance
    new_thread = Thread(thread_id=new_thread_id, user_id=current_user.id)
    
    # Add the new thread to the database
    db.add(new_thread)
    await db.commit()
    
    return {"thread_id": new_thread_id}

@app.get("/mentioned-games")
async def get_mentioned_games(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MentionedGame).where(MentionedGame.user_id == current_user.id)
    )
    games = result.scalars().all()
    return [game.game_title for game in games]

@app.post("/request-password-reset")
@limiter.limit("3/hour")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, reset_request.email)
    if not user:
        # For security reasons, always return the same message whether the user exists or not
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    reset_token = create_access_token(data={"sub": user.username, "type": "reset"}, expires_delta=timedelta(hours=1))
    
    # Store the reset token in the database
    db_token = PasswordResetToken(user_id=user.id, token=reset_token, expires_at=datetime.utcnow() + timedelta(hours=1))
    db.add(db_token)
    await db.commit()
    
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    email_body = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>This link will expire in 1 hour.</p>
        </body>
    </html>
    """
    background_tasks.add_task(send_email_async, "Password Reset Request", user.email, email_body)
    
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@app.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(reset_data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = await get_user(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify that the token exists in the database and hasn't expired
    db_token = await db.execute(select(PasswordResetToken).filter(PasswordResetToken.token == reset_data.token, PasswordResetToken.expires_at > datetime.utcnow()))
    db_token = db_token.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    db.delete(db_token)  # Remove the used token
    await db.commit()
    
    return {"message": "Password has been reset successfully"}

@app.post("/refresh-token", response_model=Token)
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    db_token = await db.execute(select(RefreshToken).filter(RefreshToken.token == token, RefreshToken.expires_at > datetime.utcnow()))
    db_token = db_token.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired refresh token")
    user = await db.get(User, db_token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(user.id)
    db.delete(db_token)
    db.add(new_refresh_token)
    await db.commit()
    return {"access_token": access_token, "refresh_token": new_refresh_token.token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(username=current_user.username, email=current_user.email)

class EmailRequest(BaseModel):
    email: EmailStr

@app.post("/request-verification-key")
@limiter.limit("3/hour")
async def request_verification_key(
    request: Request,
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Check if email already exists
    user = await get_user_by_email(db, email_request.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate a verification key
    key = secrets.token_urlsafe(8)  # 8-character key
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store the key in the database
    db_key = VerificationKey(email=email_request.email, key=key, expires_at=expires_at)
    db.add(db_key)
    await db.commit()
    
    # Send the key via email
    email_body = f"""
    <html>
        <body>
            <h2>Email Verification for GameSeeker AI</h2>
            <p>Your verification key is: <strong>{key}</strong></p>
            <p>This key will expire in 1 hour.</p>
        </body>
    </html>
    """
    background_tasks.add_task(send_email_async, "Email Verification", email_request.email, email_body)
    
    return {"message": "Verification key has been sent to your email."}

@app.on_event("startup")
async def startup():
    global graph
    graph = create_graph(AsyncSessionLocal)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)