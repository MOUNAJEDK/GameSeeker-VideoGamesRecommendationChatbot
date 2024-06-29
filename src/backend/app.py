import asyncio
import nest_asyncio
import markdown2
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import HumanMessage
from langgraph_logic.graph import graph
from langgraph_logic.utils import _print_event
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from models import Base, User, MentionedGame

from dotenv import load_dotenv
import os

load_dotenv()

# Setup asyncio for Windows
if asyncio.get_event_loop().is_closed():
    asyncio.set_event_loop(asyncio.ProactorEventLoop())
else:
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Authentication functions
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

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Input(BaseModel):
    input: str

class Output(BaseModel):
    output: List[str]

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UserOut(BaseModel):
    username: str
    email: str

# Helper functions
def format_message(content: str) -> str:
    html_content = markdown2.markdown(content)
    html_content = html_content.replace('\n', '<br>')
    return html_content

def send_reset_email(email: str, token: str):
    # In a real application, you would send an actual email.
    # For this example, we'll just print the token.
    print(f"Password reset token for {email}: {token}")

# Routes
@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

    state = {
        "messages": [HumanMessage(content=user_input)],
        "query": user_input,
        "category": "",
        "games": [],
        "details": {},
        "links": [],
        "index": 0,
        "response": []
    }

    _printed = set()
    response_list = []

    async for event in graph.astream(state, config={"recursion_limit": 50}, stream_mode="values"):
        output = _print_event(event, _printed)
        if output:
            formatted_output = format_message(output)
            response_list.append(formatted_output)

    combined_response = " ".join(response_list)

    # Save mentioned games
    for game in state["games"]:
        mentioned_game = MentionedGame(user_id=current_user.id, game_title=game)
        db.add(mentioned_game)
    await db.commit()

    return {"output": [combined_response]}

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
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reset_token = create_access_token(data={"sub": user.username, "type": "reset"}, expires_delta=timedelta(hours=1))
    
    background_tasks.add_task(send_reset_email, user.email, reset_token)
    
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
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "Password has been reset successfully"}

@app.get("/test-endpoints")
def test_endpoints():
    return {
        "message": "Here are the steps to test the backend functionalities:",
        "steps": [
            "1. Open your browser and go to http://localhost:8000/docs",
            "2. You'll see the FastAPI interactive documentation",
            "3. Test the '/register' endpoint to create a new user",
            "4. Test the '/token' endpoint to log in and get an access token",
            "5. Click the 'Authorize' button at the top and enter your access token",
            "6. Now you can test the '/chat' and '/mentioned-games' endpoints",
            "7. Test the '/request-password-reset' and '/reset-password' endpoints for password recovery"
        ]
    }

@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(username=current_user.username, email=current_user.email)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)