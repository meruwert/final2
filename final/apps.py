from fastapi import FastAPI, Path, Query, HTTPException, status, Request, Depends
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel
from app import app
from app.models import User
import fast_models
from fastDataBase import engine, SessionLocal
from sqlalchemy.orm import Session

apps = FastAPI()

fast_models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class Userapi(BaseModel):
    username: str
    first_name: str
    last_name: str
    specialization: str
    phone_number: str
    address: str
    email: str
    password: str

class UpdateUser(BaseModel):
    username: str
    first_name: str
    last_name: str
    specialization: str
    phone_number: str
    address: str
    email: str
    password: str

userlist = {}


templates = Jinja2Templates(directory='templates')
@apps.get('/', response_class=HTMLResponse)
async def doc_page(request: Request):
    return templates.TemplateResponse('fast.html', {'request': request})

@apps.get("/get-user")
def get_user(user_id: int = Query(None, description='Pass id here'), db: Session = Depends(get_db)):
    user_model = db.query(fast_models.Users).filter(fast_models.Users.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User ID not found")
    return db.query(fast_models.Users).filter(fast_models.Users.id).first()

@apps.get('/get-all-users')
def get_all(db: Session = Depends(get_db)):
    return db.query(fast_models.Users).all()

@apps.get("/get-by-username")
def get_item(username: str = Query(None, description='Input username here', min_length=2, max_length=20), db: Session = Depends(get_db)):
    user_model = db.query(fast_models.Users).filter(fast_models.Users.username == username)
    if user_model:
        return db.query(fast_models.Users).all()
    raise HTTPException(status_code=404, detail="User username not found.")

@apps.post("/create_user")
def create_user(user: Userapi, db: Session = Depends(get_db)):

    user_model = User()
    user_model.username = user.username
    user_model.first_name = user.first_name
    user_model.last_name = user.last_name
    user_model.specialization = user.specialization
    user_model.phone_number = user.phone_number
    user_model.address = user.address
    user_model.email = user.email
    user_model.password = user.password

    db.add(user_model)
    db.commit()
    return user

@apps.put("/update-user/{user_id}")
def update_user(user_id: int, user: UpdateUser, db: Session = Depends(get_db)):

    user_model = db.query(fast_models.Users).filter(fast_models.Users.id == user_id).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User ID not found")

    user_model.username = user.username
    user_model.first_name = user.first_name
    user_model.last_name = user.last_name
    user_model.specialization = user.specialization
    user_model.phone_number = user.phone_number
    user_model.address = user.address
    user_model.email = user.email
    user_model.password = user.password

    db.add(user_model)
    db.commit()
    return user

@apps.delete("/delete-user")
def delete_user(user_id: int = Query(...,description="The ID for deleting user", gt=0), db: Session = Depends(get_db)):
    user_model = db.query(fast_models.Users).filter(fast_models.Users.id == user_id).first()
    user_model = db.query(User).filter(User.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail="User ID not found")

    db.query(fast_models.Users).filter(fast_models.Users.id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()

    db.commit()
    return {"Success": "User was deleted"}

apps.mount('/marwin', WSGIMiddleware(app))
