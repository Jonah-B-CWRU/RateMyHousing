from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
from src.LoginProcessor import PasswordAttempt
import secrets
import random
#import uuid

# custom stuff
from src.Database import database_manager, User, Password, Comments, Listing, Landlord, Rating,Codes, AverageRating


app = FastAPI()
data_man = database_manager()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def add_user(username: str, password: str) -> tuple[bool,str]:
    if not username.endswith("@case.edu"):
        return False, "Username must end with @case.edu"

    data_man.connect_to_database()

    # check for both username and email
    if data_man.check_for_username(username):
        return False, "Username already exists" # uniqueness of username
    
    if data_man.check_for_email(username): #******************* change this to email when thats implemented
        return False, "Email already exists" # uniqueness of Email

    # make user and password
    user_id = secrets.token_hex(8)
    p = PasswordAttempt(user_id, password)
    new_user = User(user_id,username,"",username)
    new_password = Password(p.hash,p.salt,user_id)

    data_man.add_object(new_user)
    data_man.add_object(new_password)

    # Make code
    code = random.randrange(100000,999999)
    print(code)
    new_code = Codes(user_id,code)
    data_man.add_object(new_code)
    data_man.send_code(new_user,new_code)

    return True, "User created successfully"

def verify_login(username: str, password: str) -> bool:
    data_man.connect_to_database()
    try:
        user_data = data_man.get_user_with_username(username) # this function can fail
        pass_data = data_man.get_pass_from_user(user_data)

        p = PasswordAttempt(user_data.UserID, password, salt=pass_data.Salt)
        return p.hash == pass_data.Hash
    except TypeError as e:
        print(f"caught error {e}")
        return False

# Home Page
@app.get("/")
def index(request: Request):
    data_man.connect_to_database()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": (request.cookies.get("username") if request.cookies.get("username") != None else "Guest"),
        "title": "Home",
        "comments": data_man.get_all_from(Comments())
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
    data_man.add_object(Comments(
        secrets.token_hex(8),
        "",
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

    new_listing = Listing(
        listing_id,
        llid,
        address,
        beds,
        baths,
        sqft,
        price,
        description
    )


    data_man.add_object(new_listing)

    return templates.TemplateResponse(
        "create_listing.html",
        {
            "request": request,
            "success": "Listing created successfully!"
        }
    )


@app.get("/listings")
def view_listings(request: Request):
    data_man.connect_to_database()

    listings:list[Listing] = data_man.get_all_from(Listing()) # type: ignore

    listing_data = []

    for listing in listings:
        ratings = data_man.get_ratings_from_listing(listing)

        count = len(ratings)
        avg = round(sum(r.Rating for r in ratings) / count, 2) if count > 0 else 0

        listing_data.append({
            "listing": listing,
            "avg_rating": avg,
            "review_count": count
        })

    return templates.TemplateResponse(
        "listings.html",
        {
            "request": request,
            "listings": listing_data,
            "name": "All Listings"
        }
    )



@app.post("/add_review")
def add_review(
    request: Request,
    listing_id: str = Form(...),
    rating: int = Form(...)
):
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "message": "You must log in to leave a review.",
                "target_url": "/login"
            }
        )

    data_man.connect_to_database()

    user = data_man.get_user_with_username(username)

    review = Rating(
        secrets.token_hex(8),
        user.UserID,
        listing_id,
        rating
    )

    data_man.add_object(review)

    return RedirectResponse(url="/listings", status_code=302)

@app.get("/listing/{listingid}")
def view_one_listing(request: Request, listingid: str):
    data_man.connect_to_database()
    listing = data_man._get_document_using_id("Listing", Listing(), listingid)[0]
    comments = data_man.get_comments_from_listing(Listing(ListingID=listingid))
    
    ratings = data_man.get_ratings_from_listing(Listing(ListingID=listingid))
    count = len(ratings)
    avg = round(sum(r.Rating for r in ratings) / count, 2) if count > 0 else 0
    
    listing["avg_rating"] = avg
    listing["review_count"] = count
    
    return templates.TemplateResponse(
        "listing.html",
            {
                "request": request,
                "listing": listing,
                "comments": comments
            }
    )

@app.get("/map")
def view_listing_map(request: Request):
    data_man.connect_to_database()
    listings = data_man.get_listings()
    return templates.TemplateResponse(
        "listing_map.html",
        {
            "request": request,
            "listings": listings
        }
    )