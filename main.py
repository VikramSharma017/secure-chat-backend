# Author: Vikram Sharma
# Project: FastAPI Chat Messaging API
# Date: 2025-07-09
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import databases
import sqlalchemy

# Your existing setup
DATABASE_URL = "postgresql+asyncpg://postgres:Vikram%4017@localhost/chatdb"

SECRET_KEY = "boicandance"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("hashed_password", sqlalchemy.String),
)

rooms = sqlalchemy.Table(
    "rooms",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, unique=True),
)

messages = sqlalchemy.Table(
    "messages",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("room_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("rooms.id")),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("content", sqlalchemy.String),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime, default=datetime.utcnow),
)

engine = sqlalchemy.create_engine(DATABASE_URL.replace("+asyncpg", ""))
metadata.create_all(engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Pydantic models
class UserIn(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RoomIn(BaseModel):
    name: str

class RoomOut(BaseModel):
    id: int
    name: str

class MessageIn(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    content: str
    timestamp: datetime

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user_by_username(username: str):
    query = users.select().where(users.c.username == username)
    return await database.fetch_one(query)

async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Routes

# User registration
@app.post("/register", response_model=Token)
async def register(user_in: UserIn):
    user = await get_user_by_username(user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user_in.password)
    query = users.insert().values(username=user_in.username, hashed_password=hashed_password)
    await database.execute(query)
    access_token = create_access_token(data={"sub": user_in.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Token endpoint for login
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Create room
@app.post("/rooms", response_model=RoomOut)
async def create_room(room_in: RoomIn, current_user=Depends(get_current_user)):
    existing = await database.fetch_one(rooms.select().where(rooms.c.name == room_in.name))
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    query = rooms.insert().values(name=room_in.name)
    room_id = await database.execute(query)
    return { "id": room_id, "name": room_in.name }

# List rooms
@app.get("/rooms", response_model=List[RoomOut])
async def list_rooms(current_user=Depends(get_current_user)):
    return await database.fetch_all(rooms.select())

# Post message to room
@app.post("/rooms/{room_id}/messages", response_model=MessageOut)
async def post_message(room_id: int, message_in: MessageIn, current_user=Depends(get_current_user)):
    # Check if room exists
    room = await database.fetch_one(rooms.select().where(rooms.c.id == room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    query = messages.insert().values(
        room_id=room_id,
        user_id=current_user["id"],
        content=message_in.content,
        timestamp=datetime.utcnow()
    )
    message_id = await database.execute(query)
    return {
        "id": message_id,
        "room_id": room_id,
        "user_id": current_user["id"],
        "content": message_in.content,
        "timestamp": datetime.utcnow(),
    }

# List messages in a room
@app.get("/rooms/{room_id}/messages", response_model=List[MessageOut])
async def list_messages(room_id: int, current_user=Depends(get_current_user)):
    # Check if room exists
    room = await database.fetch_one(rooms.select().where(rooms.c.id == room_id))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    query = messages.select().where(messages.c.room_id == room_id).order_by(messages.c.timestamp)
    return await database.fetch_all(query)

# DEBUG ROUTE: List all users (for testing only)
@app.get("/debug/users")
async def list_users():
    query = users.select()
    return await database.fetch_all(query)
#Vikram Sharma