from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
from src.LoginProcessor import PasswordAttempt
import secrets

# custom stuff
from src.Database import database_manager, User, Password, Comments


app = FastAPI()
data_man = database_manager()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def add_user(username: str, password: str) -> tuple[bool,str]:
    if not username.endswith("@case.edu"):
        return False, "Username must end with @case.edu"

    data_man.connect_to_database()
    data = data_man.get_users()

    # check for both username and email
    if any(user["Username"] == username for user in data):
        return False, "Username already exists" # uniqueness of username
    
    if any(user["Email"] == username for user in data): #******************* change this to email when thats implemented
        return False, "Email already exists" # uniqueness of Email

    user_id = secrets.token_hex(8)

    p = PasswordAttempt(user_id, password)

    new_user = User(user_id,username,"",username)
    new_password = Password(p.hash,p.salt,user_id)

    data_man.add_user(new_user)
    data_man.add_passwords(new_password)

    return True, "User created successfully"

def verify_login(username: str, password: str):
    data_man.connect_to_database()

    user_data = data_man.get_users()
    pass_data = data_man.get_passwords()
    user = next((u for u in user_data if u["Username"] == username), None)
    if not user:
        return False

    pwd_entry = next((p for p in pass_data if p["UserID"] == user["UserID"]), None)
    if not pwd_entry:
        return False

    p = PasswordAttempt(user["UserID"], password, salt=pwd_entry["Salt"])
    p.genHash()
    return p.hash == pwd_entry["Hash"]

# Home Page
@app.get("/")
def index(request: Request):
    data_man.connect_to_database()
    return templates.TemplateResponse("index.html", {
        "request": request,
        # "name": (request.cookies.get("username") if request.cookies.get("username") != None else "none"),
        "name": "Guest",
        "title": "Home",
        "comments": data_man.get_comments()
        })

# Page to create new user, GET
@app.get("/create")
def create_user_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request, "error": None, "success": None})

# POST Request for new user
@app.post("/create")
def create_user_post(request: Request, username: str = Form(...), password: str = Form(...)):
    success, msg = add_user(username, password)
    return templates.TemplateResponse(
        "create.html",
        {"request": request, "error": None if success else msg, "success": msg if success else None}
    )

# Login page
@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

# Login submission
@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    #success
    if verify_login(username, password):
        # Go to dashboard
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="username", value=username)
        return response
    else: #unsuccessful
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

# Dashboard only available if logged in.
@app.get("/dashboard")
def dashboard(request: Request):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "message": "You must log in to access the dashboard.",
                "target_url": "/"
            }
        )
    return templates.TemplateResponse("dashboard.html", {"request": request, "name": username})


# Logs out user
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("username")
    return response

@app.get("/comment")
def comment(request: Request):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "message": "You must log in to access the dashboard.",
                "target_url": "/"
            }
        )
    return templates.TemplateResponse("comment.html", {"request": request, "name": username})
@app.post("/comment")
def comment_post(request: Request, comment: str = Form(...)):
    # print(comment)
    data_man.add_comment(Comments(
        secrets.token_hex(8),
        "",
        "",
        comment
        ))
    return templates.TemplateResponse(
        "redirect.html",
            {
                "request": request,
                "message": "Comment posted.",
                "target_url": "/dashboard"
            }
    )