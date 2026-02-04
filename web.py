from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
from LoginProcessor import PasswordAttempt
import secrets

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

USERS_FILE = Path("users.json")


def load_users_json():
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text())
        except json.JSONDecodeError:
            data = {"users": [], "passwords": []}
    else:
        data = {"users": [], "passwords": []}

    if "users" not in data:
        data["users"] = []
    if "passwords" not in data:
        data["passwords"] = []

    return data

def save_users_json(data):
    USERS_FILE.write_text(json.dumps(data, indent=4))

def add_user(username: str, password: str):
    if not username.endswith("@case.edu"):
        return False, "Username must end with @case.edu"

    data = load_users_json()
    if any(u["username"] == username for u in data["users"]):
        return False, "Username already exists" # uniqueness of username

    user_id = secrets.token_hex(8)

    p = PasswordAttempt(user_id, password)
    p.genSalt()
    p.genHash()

    data["users"].append({
        "user_id": user_id,
        "username": username,
        "email": username,
        "landlord_account": None
    })
    data["passwords"].append({
        "user_id": user_id,
        "hash": p.hash,
        "salt": p.salt
    })
    save_users_json(data)
    return True, "User created successfully"

def verify_login(username: str, password: str):
    data = load_users_json()
    user = next((u for u in data["users"] if u["username"] == username), None)
    if not user:
        return False

    pwd_entry = next((p for p in data["passwords"] if p["user_id"] == user["user_id"]), None)
    if not pwd_entry:
        return False

    p = PasswordAttempt(user["user_id"], password, salt=pwd_entry["salt"])
    p.genHash()
    return p.hash == pwd_entry["hash"]

# Home Page
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "name": "Guest", "title": "Home"})

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
