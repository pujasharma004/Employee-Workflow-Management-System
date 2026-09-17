from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import engine, Base, get_db
from models import User, Department, Request
from schemas import (RequestCreate,UserCreate,DepartmentCreate,RequestResponse,RegisterRequest,LoginRequest,LoginResponse)
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from passlib.context import CryptContext
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(user_id: int, role: str):
    payload = {
        "user_id": user_id,
        "role": role
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM

        
    )

    return token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/register")
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }

@app.post("/login", response_model=LoginResponse)
def login(user_data: LoginRequest, db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not pwd_context.verify(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate JWT token
    access_token = create_access_token(
        user.id,
        user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



@app.post("/requests")
def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db)
):
    department = db.query(Department).filter(
        Department.name == request_data.category
    ).first()

    if not department:
        return {
            "message": "No department found for this category"
        }

    if request_data.priority == "High":
        sla_hours = 4
    elif request_data.priority == "Medium":
        sla_hours = 8
    else:
        sla_hours = 24

    sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours)

    new_request = Request(
        title=request_data.title,
        description=request_data.description,
        category=request_data.category,
        priority=request_data.priority,
        user_id=request_data.user_id,
        department_id=department.id,
        sla_deadline=sla_deadline
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {
        "message": "Request created successfully",
        "request_id": new_request.id,
        "title": new_request.title,
        "status": new_request.status,
        "department": department.name,
        "user_id": new_request.user_id,
        "sla_deadline": new_request.sla_deadline
    }

@app.get("/requests", response_model=list[RequestResponse])
def get_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    requests = db.query(Request).all()

    return requests

@app.get("/requests/{request_id}", response_model=RequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    request = db.query(Request).filter(
        Request.id == request_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    return request

class RequestUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None

@app.patch("/requests/{request_id}")
def update_request(
    request_id: int,
    update_data: RequestUpdate,
    db: Session = Depends(get_db)
):
    request = db.query(Request).filter(
        Request.id == request_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    if update_data.status is not None:
        request.status = update_data.status

    if update_data.priority is not None:
        request.priority = update_data.priority

    db.commit()
    db.refresh(request)

    return {
        "message": "Request updated successfully",
        "request_id": request.id,
        "status": request.status,
        "priority": request.priority
    }

@app.post("/users")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }

@app.post("/departments")
def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db)
):
    new_department = Department(
        name=department_data.name
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    return {
        "message": "Department created successfully",
        "department_id": new_department.id,
        "name": new_department.name
    }

@app.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db)
):
    total = db.query(Request).count()

    open_requests = db.query(Request).filter(
        Request.status == "Open"
    ).count()

    in_progress = db.query(Request).filter(
        Request.status == "In Progress"
    ).count()

    resolved = db.query(Request).filter(
        Request.status == "Resolved"
    ).count()

    high_priority = db.query(Request).filter(
        Request.priority == "High"
    ).count()

    return {
        "total_requests": total,
        "open_requests": open_requests,
        "in_progress": in_progress,
        "resolved": resolved,
        "high_priority_requests": high_priority
    }