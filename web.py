from fastapi import FastAPI, Form, Request # type: ignore
from fastapi.responses import RedirectResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from pathlib import Path
import secrets
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.Database import database_manager, User, Password, Comments, Listing, Landlord, Rating
from src.LoginProcessor import PasswordAttempt

app = FastAPI()
data_man = database_manager()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def add_user(username: str, password: str) -> tuple[bool, str]:
    if not username.endswith("@case.edu"):
        return False, "Username must end with @case.edu"

    data_man.connect_to_database()

    if data_man.check_for_username(username):
        return False, "Username already exists"

    if data_man.check_for_email(username):
        return False, "Email already exists"

    user_id = secrets.token_hex(8)
    p = PasswordAttempt(user_id, password)

    new_user = User(user_id, username, "", username)
    new_password = Password(p.hash, p.salt, user_id)

    data_man.add_user(new_user)
    data_man.add_passwords(new_password)

    return True, "User created successfully"

def verify_login(username: str, password: str) -> bool:
    data_man.connect_to_database()
    try:
        user_data = data_man.get_user_with_username(username)
        pass_data = data_man.get_pass_from_user(user_data)
        p = PasswordAttempt(user_data.UserID, password, salt=pass_data.Salt)
        return p.hash == pass_data.Hash
    except TypeError:
        return False

@app.get("/")
def index(request: Request):
    data_man.connect_to_database()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "name": request.cookies.get("username") or "Guest",
            "title": "Home",
            "comments": data_man.get_comments()
        }
    )

@app.get("/create")
def create_user_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request, "error": None, "success": None})

@app.post("/create")
def create_user_post(request: Request, username: str = Form(...), password: str = Form(...)):
    success, msg = add_user(username, password)
    return templates.TemplateResponse(
        "create.html",
        {"request": request, "error": None if success else msg, "success": msg if success else None}
    )

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_login(username, password):
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="username", value=username)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/dashboard")
def dashboard(request: Request):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    return templates.TemplateResponse("dashboard.html", {"request": request, "name": username})

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("username")
    return response

@app.get("/create_listing")
def create_listing_form(request: Request):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to create a listing.", "target_url": "/login"}
        )
    return templates.TemplateResponse("create_listing.html", {"request": request, "error": None})

@app.post("/create_listing")
def create_listing(
    request: Request,
    llid: str = Form(...),
    address: str = Form(...),
    beds: int = Form(...),
    baths: int = Form(...),
    sqft: int = Form(...),
    price: float = Form(...),
    description: str = Form("")
):
    data_man.connect_to_database()
    listing_id = secrets.token_hex(8)
    created_at = datetime.utcnow().isoformat() + "Z"

    new_listing = Listing(
        listing_id,
        llid,
        address,
        beds,
        baths,
        sqft,
        price,
        description,
        created_at
    )

    data_man.add_listing(new_listing)

    return templates.TemplateResponse(
        "create_listing.html",
        {"request": request, "success": "Listing created successfully!"}
    )

@app.get("/listings")
def view_listings(request: Request):
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    data_man.connect_to_database()
    listings = data_man.get_all_listings()
    listing_data = []

    for listing in listings:
        ratings = data_man.get_ratings_from_listing(listing)
        comments = data_man.get_comments_from_listing(listing)

        comments_with_users = []
        for c in comments:
            try:
                user = data_man.get_user_from_id(c.UserID)
                # Convert comment timestamp to Eastern Time
                if c.CreatedAt:
                    utc_dt = datetime.fromisoformat(c.CreatedAt.replace("Z", "")).replace(tzinfo=timezone.utc)
                    eastern_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
                    created_str = eastern_dt.strftime("%m/%d/%Y, %I:%M %p")
                else:
                    created_str = ""
                comments_with_users.append({
                    "Content": c.Content,
                    "Username": user.Username,
                    "CreatedAt": created_str
                })
            except TypeError:
                comments_with_users.append({
                    "Content": c.Content,
                    "Username": "Unknown",
                    "CreatedAt": ""
                })

        count = len(ratings)
        avg = round(sum(r.Rating for r in ratings) / count, 2) if count > 0 else 0

        # Convert listing timestamp to Eastern Time
        created_str = ""
        if listing.CreatedAt:
            try:
                utc_dt = datetime.fromisoformat(listing.CreatedAt.replace("Z", "")).replace(tzinfo=timezone.utc)
                eastern_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
                created_str = eastern_dt.strftime("%m/%d/%Y, %I:%M %p")
            except:
                created_str = listing.CreatedAt

        listing_data.append({
            "listing": listing,
            "avg_rating": avg,
            "review_count": count,
            "created_at": created_str,
            "comments": comments_with_users
        })

    return templates.TemplateResponse(
        "listings.html",
        {"request": request, "listings": listing_data, "name": "All Listings"}
    )

@app.post("/add_review")
def add_review(request: Request, listing_id: str = Form(...), rating: int = Form(...)):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to leave a review.", "target_url": "/login"}
        )

    data_man.connect_to_database()
    user = data_man.get_user_with_username(username)

    review = Rating(secrets.token_hex(8), user.UserID, listing_id, rating)
    data_man.add_rating(review)

    return RedirectResponse(url="/listings", status_code=302)

from datetime import datetime, timezone

@app.post("/add_comment")
def add_comment(request: Request, listing_id: str = Form(...), comment: str = Form(...)):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to leave a comment.", "target_url": "/login"}
        )

    data_man.connect_to_database()
    user = data_man.get_user_with_username(username)

    now_utc = datetime.now(timezone.utc).isoformat()  # store timestamp in UTC

    new_comment = Comments(
        CommentId=secrets.token_hex(8),
        ConnectedCommentID="",
        ListingID=listing_id,
        UserID=user.UserID,
        Content=comment,
        CreatedAt=now_utc  # <-- set timestamp
    )

    data_man.add_comment(new_comment)
    return RedirectResponse(url="/listings", status_code=302)