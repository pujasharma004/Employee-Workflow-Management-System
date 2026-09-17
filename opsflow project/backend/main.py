from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import engine, Base, get_db
from models import User, Department, Request
from schemas import RequestCreate, UserCreate, DepartmentCreate,  RequestResponse
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

Base.metadata.create_all(bind=engine)

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
    db: Session = Depends(get_db)
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