from fastapi import FastAPI, Form, Request # type: ignore
from fastapi.responses import RedirectResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import secrets
import requests



# custom stuff
from src.Database import database_manager, User, Password, Comments, Listing, Landlord, Rating,Codes, AverageRating
from src.LoginProcessor import PasswordAttempt
from src.Caching import cache_manager
import random



TAG_GROUPS = {
    "value": ["Good Value", "Overpriced"],
    "noise": ["Quiet", "Noisy"],
    "condition": ["Clean", "Dirty"],
    "landlord": ["Responsive Landlord", "Unresponsive Landlord"]
}

app = FastAPI()
data_man = database_manager()
cache_man = cache_manager()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def add_user(username: str, password: str) -> tuple[bool, str]:
    """
    adds user to database\n
    **not cached**
    """
    if not username.endswith("@case.edu"):
        return False, "Username must end with @case.edu"

    data_man.connect_to_database()

    if data_man.check_for_username(username):
        return False, "Username already exists"
      
    if data_man.check_for_email(username):
        return False, "Email already exists"
    
    
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
    """
    verifies login by checking for valid user and valid password \n
    **not cached**
    """
    data_man.connect_to_database()
    try:
        user_data = data_man.get_user_with_username(username)
        pass_data = data_man.get_pass_from_user(user_data)
        p = PasswordAttempt(user_data.UserID, password, salt=pass_data.Salt)
        return (p.hash == pass_data.Hash) and user_data.Activated
    except TypeError:
        return False

def make_all_listing_data(listings: list[Listing]) -> list:
    """
    uses cached data to make all listing data
    """
    listing_data = []
    for listing in listings:
        if f"listing_{listing.ListingID}" in cache_man.all_refrences: 
            cache_data = cache_man.get_cache(f"listing_{listing.ListingID}")
            if cache_data.cache_max_age > datetime.now():
                # use cached data
                raw_data:dict = cache_data.cache_data
                meta_listing:dict = raw_data["meta_listing"]
                comments_with_users:list = raw_data["comments"]
            else:
                meta_listing, comments_with_users = make_specific_listing_data(listing)
                # pack into cached data
                data = {"meta_listing":meta_listing,"comments":comments_with_users}
                cache_man.add_to_cache(data,f"listing_{listing.ListingID}")
        else:
            meta_listing, comments_with_users = make_specific_listing_data(listing)
            # pack into cached data
            data = {"meta_listing":meta_listing,"comments":comments_with_users}
            cache_man.add_to_cache(data,f"listing_{listing.ListingID}")

        listing_data.append({
            "listing": meta_listing,
            "comments": comments_with_users
        })
    return listing_data

def make_specific_listing_data(listing: Listing):
    # meta listing creation
    meta_listing = listing.as_dict()
    if data_man.check_for_average_rating(listing):
        data_man.update_average_rating(listing) # makes it
    comments = data_man.get_comments_from_listing(listing)
    ar = data_man.get_average_rating_from_listing(listing)
    
    # new variables being sent to website
    meta_listing["avg_rating"] = round(ar.AverageRating, 2)
    meta_listing["review_count"] = ar.NumberOfRatings
    created_str = ""
    if listing.CreatedAt:
        try:
            utc_dt = datetime.fromisoformat(listing.CreatedAt.replace("Z", "")).replace(tzinfo=timezone.utc)
            eastern_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))
            created_str = eastern_dt.strftime("%m/%d/%Y, %I:%M %p")
        except:
            created_str = listing.CreatedAt
    meta_listing["CreatedAt"] = created_str

    # comments
    comments_with_users = []
    for c in comments:
        try:
            user = data_man.get_user_from_comments(c)
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
                "Tags": c.Tags if c.Tags else []
            })
        except TypeError as e:
            print(f"user failed: {e}")
            comments_with_users.append({
                "Content": c.Content,
                "Username": "Unknown",
                "CreatedAt": ""
                "Tags": c.Tags if c.Tags else []
            })
    return (meta_listing,comments_with_users)

@app.get("/")
def index(request: Request):
    data_man.connect_to_database()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": (request.cookies.get("username") if request.cookies.get("username") != None else "Guest"),
        "title": "Home",
        "comments": data_man.get_all_from(Comments())
        })

@app.get("/create")
def create_user_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request, "error": None, "success": None})

@app.post("/create")
def create_user_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    creates a user in database \n
    **not cached**
    """
    success, msg = add_user(username, password)
    return templates.TemplateResponse(
        "create.html",
        {"request": request, "error": None if success else msg, "success": msg if success else None}
    )

@app.get("/code")
def get_code_form(request: Request):
    return templates.TemplateResponse("code_input.html", {"request": request, "error": None, "success": None})

@app.post("/code")
def verify_code_form(request: Request, email: str = Form(...), code: str = Form(...)):
    """
    verifies code \n
    **not cached**
    """
    data_man.connect_to_database()
    user = data_man.get_user_with_email(email)
    
    if data_man.verify_code(user,int(code)):
        user.Activated = True
        data_man.update_object(user)
        data_man.recursive_deletion(data_man.get_code_from_user(user))
    return templates.TemplateResponse("code_input.html", {"request": request, "error": None, "success": None})

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    verifies login by checking for valid user and valid password \n
    **not cached**
    """
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
    return templates.TemplateResponse(
            "comment.html",
            {
                "request": request,
                "name": username,
                "TAG_GROUPS": TAG_GROUPS    # REQUIRED
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
    """
    creates listing with relevent infromation \n
    **Updates cache**
    """
    data_man.connect_to_database()
    listing_id = secrets.token_hex(8)
    created_at = datetime.now(timezone.utc).isoformat() + "Z"
    
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q":address+",Cuyahoga County","format":"json"},
            headers={
                "User-Agent": "RateMyHousing Application"
            }
            )
        potential_coords = response.json()[0]

        new_listing = Listing(
            listing_id,
            llid,
            address,
            beds,
            baths,
            sqft,
            price,
            description,
            created_at,
            potential_coords["lat"],
            potential_coords["lon"],
        )
    except:
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


    data_man.add_object(new_listing)
    data_man.update_average_rating(Listing(listing_id))

    # cache it
    meta_listing, comments_with_users = make_specific_listing_data(new_listing)
    data = {"meta_listing":meta_listing,"comments":comments_with_users}
    ref = cache_man.add_to_cache(data, f"listing_{new_listing.ListingID}")
    cache_man.all_refrences[f"listing_{new_listing.ListingID}"] = ref

    return templates.TemplateResponse(
        "create_listing.html",
        {"request": request, "success": "Listing created successfully!"}
    )

@app.get("/listings")
def view_listings(request: Request):
    """
    Gets all listings \n
    **Is cached**
    """
    data_man.connect_to_database()

    listings:list[Listing] = data_man.get_all_from(Listing())
    listing_data = make_all_listing_data(listings) # has built in cach checking and renewing

    return templates.TemplateResponse(
        "listings.html",
        {"request": request, "listings": listing_data, "name": "All Listings"}
    )

@app.post("/add_review")
def add_review(
    request: Request,
    listing_id: str = Form(...),
    rating: int = Form(...)
):
    """
    Adds a review \n
    **Updates cache**
    """
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
        RatingID=secrets.token_hex(8),
        UserID=user.UserID,
        ListingID=listing_id,
        Rating=rating
    )

    data_man.add_object(review)

    # update average rating
    data_man.update_average_rating(Listing(listing_id))

    # update cache
    ref = cache_man.all_refrences[f"listing_{listing_id}"] 
    listing = data_man.get_listing_from_rating(review)
    meta_listing, comments_with_users = make_specific_listing_data(listing)
    data = {"meta_listing":meta_listing,"comments":comments_with_users}
    ref = cache_man.update_cache(data, ref)
    cache_man.all_refrences[f"listing_{listing_id}"] = ref

    return RedirectResponse(url="/listings", status_code=302)


@app.post("/add_comment")
def add_comment(
    request: Request,
    listing_id: str = Form(...),
    comment: str = Form(...),
    tags_noise: list[str] = Form([]),
    tags_condition: list[str] = Form([]),
    tags_landlord: list[str] = Form([]),
    tags_value: list[str] = Form([])
):
    """
    Adds a comment \n
    **Updates cache**
    """
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to leave a comment.", "target_url": "/login"}
        )
    
    # Combine all selected tags
    selected_tags = tags_noise + tags_condition + tags_landlord + tags_value

    # Enforce max 1 per group
    if len(tags_noise) > 1 or len(tags_condition) > 1 or len(tags_landlord) > 1 or len(tags_value) > 1:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You can only select one tag per group.", "target_url": f"/listing/{listing_id}"}
        )

    # Validate against TAG_GROUPS
    valid, msg = validate_tags(selected_tags)
    if not valid:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": msg, "target_url": f"/listing/{listing_id}"}
        )
    

    data_man.connect_to_database()
    user = data_man.get_user_with_username(username)

    if not user:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to leave a comment.", "target_url": "/login"}
        )

    now_utc = datetime.now(timezone.utc).isoformat()  # store timestamp in UTC

    new_comment = Comments(
        CommentId=secrets.token_hex(8),
        ConnectedCommentID="",
        ListingID=listing_id,
        UserID=user.UserID,
        Content=comment,
        CreatedAt=now_utc
        Tags=selected_tags
    )

    data_man.add_object(new_comment)

   
    # update cache
    ref = cache_man.all_refrences[f"listing_{listing_id}"] 
    listing = data_man.get_listing_from_comments(new_comment)
    meta_listing, comments_with_users = make_specific_listing_data(listing)
    data = {"meta_listing":meta_listing,"comments":comments_with_users}
    ref = cache_man.update_cache(data, ref)
    cache_man.all_refrences[f"listing_{listing_id}"] = ref

    return RedirectResponse(url="/listings", status_code=302)

@app.get("/listing/{listingid}")
def view_one_listing(request: Request, listingid: str):
    """
    views one listing \n
    **Is cached**
    """
    data_man.connect_to_database()

    # cache real
    if f"listing_{listingid}" in cache_man.all_refrences: 
        cache_data = cache_man.get_cache(f"listing_{listingid}")
        if cache_data.cache_max_age > datetime.now():
            # use cached data
            raw_data:dict = cache_data.cache_data
            meta_listing:dict = raw_data["meta_listing"]
            comments_with_users:list = raw_data["comments"]
        else:
            listing = data_man._get_document_using_id("Listing", Listing(), listingid)[0]
            listing_object = Listing.from_dict(listing)
            meta_listing, comments_with_users = make_specific_listing_data(listing_object)
        # pack into cached data
            data = {"meta_listing":meta_listing,"comments":comments_with_users}
            cache_man.add_to_cache(data,f"listing_{listingid}")
    else:
        listing = data_man._get_document_using_id("Listing", Listing(), listingid)[0]
        listing_object = Listing.from_dict(listing)
        meta_listing, comments_with_users = make_specific_listing_data(listing_object)
        # pack into cached data
        data = {"meta_listing":meta_listing,"comments":comments_with_users}
        cache_man.add_to_cache(data,f"listing_{listingid}")
    
        
    return templates.TemplateResponse(
        "listing.html",
            {
                "request": request,
                "listing": meta_listing,
                "comments": comments_with_users
            }
    )

@app.get("/map")
def view_listing_map(request: Request):
    data_man.connect_to_database()
    listings = [listdict.as_dict() for listdict in data_man.get_all_from(Listing())]
    return templates.TemplateResponse(
        "listing_map.html",
        {
            "request": request,
            "listings": listings
        }
    )



def validate_tags(selected_tags: list[str]) -> tuple[bool, str]:
    if len(selected_tags) > 4:
        return False, "You can select up to 4 tags."

    used_groups = set()

    for tag in selected_tags:
        found = False
        for group, options in TAG_GROUPS.items():
            if tag in options:
                if group in used_groups:
                    return False, f"Only one tag allowed from '{group}' category."
                used_groups.add(group)
                found = True
                break
        if not found:
            return False, f"Invalid tag: {tag}"

    return True, ""