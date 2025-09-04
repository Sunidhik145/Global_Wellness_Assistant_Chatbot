from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import datetime
from typing import Optional

# ------------------ Config ------------------
SECRET_KEY = "CHANGE_THIS_TO_A_RANDOM_SECRET_IN_PRODUCTION"   # <<-- change & move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token lifetime

# ------------------ DB setup (SQLite + SQLAlchemy) ------------------
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------ Models ------------------
class User(Base):
    __tablename__ = "users"   
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)  # email as username
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    age_group = Column(String, nullable=True)
    gender = Column(String, nullable=True)  
    preferred_language = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# ------------------ Security utils ------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------ FastAPI app ------------------
app = FastAPI(title="🌿 Global Wellness Chatbot Backend (with JWT)")

# ------------------ Pydantic Schemas ------------------
class RegisterModel(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    preferred_language: Optional[str] = None

class ProfileUpdateModel(BaseModel):
    name: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    preferred_language: Optional[str] = None

# ------------------ DB dependency ------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ Helper DB functions ------------------
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, name: str = None,
                age_group: str = None, gender: str = None,
                preferred_language: str = None):
    hashed_pw = get_password_hash(password)
    user = User(
        username=username,
        hashed_password=hashed_pw,
        name=name,
        age_group=age_group,
        gender=gender,
        preferred_language=preferred_language
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ------------------ Auth endpoints ------------------
@app.post("/register", status_code=201)
def register_user(payload: RegisterModel, db: Session = Depends(get_db)):
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = create_user(
        db,
        username=payload.username,
        password=payload.password,
        name=payload.name,
        age_group=payload.age_group,
        gender=payload.gender,
        preferred_language=payload.preferred_language
    )
    return {
        "msg": "User registered successfully",
        "user_id": user.id,
        "name": user.name,
        "age_group": user.age_group,
        "gender": user.gender,
        "preferred_language": user.preferred_language
    }

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "age_group": user.age_group,
        "gender": user.gender,
        "preferred_language": user.preferred_language
    }

# ------------------ Token / current user helper ------------------
def get_current_username(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (invalid or expired token)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = get_current_username(token)
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ------------------ Protected routes ------------------
@app.get("/me")
def read_current_user(current_username: str = Depends(get_current_username)):
    return {"username": current_username}

@app.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "name": user.name,
        "age_group": user.age_group,
        "gender": user.gender,
        "preferred_language": user.preferred_language
    }

@app.put("/profile/{user_id}")
def update_profile(
    user_id: int,
    payload: ProfileUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.name is not None:
        user.name = payload.name
    if payload.age_group is not None:
        user.age_group = payload.age_group
    if payload.gender is not None:
        user.gender = payload.gender
    if payload.preferred_language is not None:
        user.preferred_language = payload.preferred_language
    
    db.commit()
    return {
        "msg": "Profile updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "age_group": user.age_group,
            "gender": user.gender,
            "preferred_language": user.preferred_language
        }
    }

@app.get("/chat")
def chat(message: str, current_username: str = Depends(get_current_username)):
    reply = f"Echo from bot to {current_username}: {message}"
    return {"user": current_username, "response": reply}

# ------------------ Unprotected quick health endpoint ------------------
@app.get("/")
def root():
    return {"msg": "Global Wellness Chatbot Backend is running. Use /token to login."}
