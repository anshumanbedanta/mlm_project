from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, utils
from .database import engine, SessionLocal

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MLM Dashboard API",
    description="API for user registration and login with sponsor network.",
    version="1.0.0"
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def assign_position(db: Session, sponsor_id: int):
    children = db.query(models.User).filter(models.User.parent_id == sponsor_id).all()

    if len(children) == 0:
        return sponsor_id, "left"
    elif len(children) == 1:
        # Check existing child position to properly assign the opposite
        if children[0].position == "left":
            return sponsor_id, "right"
        else:
            return sponsor_id, "left"
    else:
        raise Exception("Both positions filled")

# --- Endpoints ---
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Name already registered")
        
    parent_id = None
    position = None

    # Check if sponsor exists, if a sponsor_id is provided
    if user.sponsor_id:
        sponsor = db.query(models.User).filter(models.User.id == user.sponsor_id).first()
        if not sponsor:
            raise HTTPException(status_code=400, detail="Sponsor ID does not exist")
            
        try:
            parent_id, position = assign_position(db, user.sponsor_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Hash the password and save the new user
    hashed_pw = utils.get_password_hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        password_hash=hashed_pw,
        sponsor_id=user.sponsor_id,
        parent_id=parent_id,
        position=position
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    # Authenticate user
    db_user = db.query(models.User).filter(models.User.name == user.name).first()
    if not db_user or not utils.verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect name or password"
        )
    
    # In a real app, you would return a JWT token here.
    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "name": db_user.name
    }

@app.get("/users", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
