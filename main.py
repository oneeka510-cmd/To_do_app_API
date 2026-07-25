from fastapi import FastAPI, Depends, HTTPException,status, Query
from datetime import datetime
from pydantic import BaseModel,Field
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Boolean,DateTime
from sqlalchemy.orm import declarative_base,sessionmaker,Session
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
load_dotenv()
import os

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")        
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))



# .env file
#       │
#       ▼
# load_dotenv()
#       │
#       ▼
# Environment Variables
#       │
#       ▼
# os.getenv("DATABASE_URL")


engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(bind=engine)

app=FastAPI(title="Task Manager API")

Base=declarative_base()



#Creating a password hasher 
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
#TESTING
# password = "hello12345"
# hashed_password = pwd_context.hash(password)
# print(hashed_password)
# print(pwd_context.verify("hello12345", hashed_password))
# # # True
# print(pwd_context.verify("wrongpassword", hashed_password))
# # False


#dB Tables
  #Task Table
class Task(Base):
    __tablename__="tasks"
    id=Column(Integer,primary_key=True)
    title=Column(String(100))
    completed=Column(Boolean)
    created_at=Column(DateTime)
#Testing dB connection:
# session = SessionLocal()
# tasks=session.query(Task).all()
# print(tasks)


  #User Table
class User(Base):
     __tablename__="users"
     id=Column(Integer,primary_key=True)
     username=Column(String(50),unique=True, nullable=False)
     hashed_password=Column(String(255),nullable=False)
# #Testing dB connection:
# session = SessionLocal()
# tasks=session.query(Task).all()
# print(tasks)





# DTOs:
  # Task DTOs
class TaskCreateDTO(BaseModel):
    title:str =Field(min_length=2,max_length=100)


class TaskResponseDTO(BaseModel):
    id:int
    title:str
    completed: bool
    created_at: datetime


  #User DTOs
class UserCreateDTO(BaseModel):
    username:str = Field(min_length=2,max_length=50,description="A unique name chosen by the user")
    password:str=Field(min_length=8)


class UserResponseDTO(BaseModel):
    username:str=Field(description="Username stored in the dB")
    id:int =Field(description="Id of this username stored in dB")


class LoginDTO(BaseModel):
    username: str = Field(
        min_length=2,
        max_length=50,
        description="Username used for login"
    )
    password: str = Field(
        min_length=8,
        description="User password"
    )


#This is ok for patch not put
# class TaskUpdateDTO(BaseModel):
#     title:Optional[str] 
#     completed:Optional[bool] 



# because PUT expects the client to send the complete editable resource.
class TaskUpdateDTO(BaseModel):
    title: str
    completed:bool




#Dependency Injection:
def get_db():
    try:
        session=SessionLocal()
        yield session
    finally:
        session.close()




#JWT Authentication
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")
# Login endpoint → creates JWTs. 
# oauth2_scheme → extracts JWTs from incoming requests.
#"When someone needs a token, they should obtain it from the /login endpoint."
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
        user_id=int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    user = session.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    return user




@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username
    }




# #Get all the tasks from dB
# @app.get("/tasks")
# def get_tasks(session:Session=Depends(get_db)):
#     tasks=session.query(Task).all()
#     return tasks   
# # session: Session = Depends(get_db)
# # "The session parameter is a Session, and FastAPI should obtain it by calling get_db."


# Field() → validation inside models.
# Query() → validation for URL query parameters.

#Modifying get tasks endpoint for filtering,sorting and pagination
@app.get("/tasks",response_model=list[TaskResponseDTO])
def get_tasks(completed:bool|None=None,
              title:str |None=None,
              sort_by:str |None=None,
              order: str | None = None,
              limit: int | None = Query(None, ge=1),
              offset: int | None = Query(None, ge=0),
              session:Session=Depends(get_db)):
    
    query=session.query(Task)

    if completed is not None:
        query=query.filter(Task.completed==completed)

    if title is not None:
       query=query.filter(Task.title.ilike(f"%{title}%"))

    if sort_by is not None:

         sort_columns = {
    "id": Task.id,
    "title": Task.title,
    "completed": Task.completed,
    "created_at":Task.created_at
    }

    column = sort_columns.get(sort_by)

    if column is not None:
        if order is not None:
            order = order.lower()

        if order == "desc":
            query = query.order_by(column.desc())
        else:
           query = query.order_by(column)

    if limit is not None:
       query= query.limit(limit)

    if offset is not None:
        query=query.offset(offset)

    tasks=query.all()
    return tasks





#Get one task from db based on Id
# Either id exists or not 
@app.get("/tasks/{id}",response_model=TaskResponseDTO)
def get_a_task(id:int,session:Session=Depends(get_db)):
    query= session.query(Task).filter(Task.id==id)  # creating a query object 
   
    task=query.first() # getting task from dB in task variable
    if task is not None:   
         return task
    else:    # if task is None 
        raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
   
    


#Adding a task to dB 
@app.post("/tasks",response_model=TaskResponseDTO,status_code=status.HTTP_201_CREATED)
def add_task(data:TaskCreateDTO,session:Session=Depends(get_db)):
    new_task=Task(title=data.title)
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task
# The response model is doing two jobs:
#  Converts ORM objects into serializable data.
#  Filters out fields you don't want to expose.





#find task from the id sent, if task doesnt exist return 404 
# if task exists change title using orm then completed status using ORM
@app.put("/tasks/{id}",response_model=TaskResponseDTO,status_code=status.HTTP_200_OK)
def update_task(id:int,data:TaskUpdateDTO,session:Session=Depends(get_db)):
    task=session.query(Task).filter(Task.id==id).first()
    if task is None:
        raise HTTPException(
            status_code= 404,
            detail="Task Not Found"
        )
    
    task.title = data.title
    task.completed = data.completed
    session.commit()
    session.refresh(task)
    return task
#     Notice there is no: Task(...)
#     session.add(...)  during an update.




#first check if id exists if yes then session.delete task
@app.delete("/tasks/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_a_task(id:int,session:Session=Depends(get_db)):
    task=session.query(Task).filter(Task.id==id).first()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task does not exist"
        )
    session.delete(task)
    session.commit()
    
    return

# User logs in
#         ↓
# Username exists?
#         ↓
# Password correct?
#         ↓
# Create JWT
#         ↓
# Send JWT to frontend
#         ↓
# Frontend stores JWT
#         ↓
# Frontend sends JWT with every request
#         ↓
# Server verifies JWT
#         ↓
# Allow access





@app.post("/register",response_model=UserResponseDTO,status_code=status.HTTP_201_CREATED)
def add_user(data:UserCreateDTO,session:Session=Depends(get_db)):
    #check if username exists:
    user=session.query(User).filter(User.username==data.username).first()
    if user is not None:
        raise HTTPException(
            status_code= 409,
            detail="Username exists, please choose another one"
        )
    
    hashed_password = pwd_context.hash(data.password)
    new_user = User(username=data.username,hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user



# def user_login(data:LoginDTO,session:Session=Depends(get_db)):
@app.post("/login")
def user_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    #check username exists or not:
    user=session.query(User).filter(User.username==form_data.username).first()
    if user is None:
        raise HTTPException(
            status_code= 401,
            detail= "Invalid username or password"
        )
    #check if password matches or not
    password_matches=pwd_context.verify(form_data.password,user.hashed_password)
    if not password_matches:
        raise HTTPException(
            status_code= 401,
            detail="Invalid username or password"
        )
    expire = datetime.now(timezone.utc) + timedelta(
    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
     )
    
    payload={
        "sub": str(user.id),
        "exp": expire
    }

    access_token = jwt.encode(
    payload,
    SECRET_KEY,
    algorithm=ALGORITHM
)
    return {
        "access_token": access_token,
        "token_type":"bearer"
    }



# Register
#     ↓
# Hash password
#     ↓
# Store in database
#     ↓
# Login
#     ↓
# Verify password
#     ↓
# Generate JWT
#     ↓
# Return JWT
#     ↓
# Frontend stores JWT
#     ↓
# Frontend sends JWT in Authorization header
#     ↓
# FastAPI extracts JWT
#     ↓
# Decode JWT
#     ↓
# Get user ID
#     ↓
# Query database
#     ↓
# Current user



# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     session: Session = Depends(get_db)
# ):









