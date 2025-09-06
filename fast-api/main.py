from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from database import init_db, get_session
from models import Task
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")
@app.on_event("startup")
def on_startup():
    init_db()
@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    tasks = session.exec(select(Task)).all()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})
@app.post("/add", response_class=HTMLResponse)
def add_task(request: Request, title: str, session: Session = Depends(get_session)):
    task = Task(title=title)
    session.add(task)
    session.commit()
    session.refresh(task)
    tasks = session.exec(select(Task)).all()
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks})
