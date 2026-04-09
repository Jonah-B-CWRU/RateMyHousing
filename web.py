from typing import Any

from fastapi import FastAPI, Form, Request # type: ignore
from fastapi.responses import RedirectResponse,FileResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import secrets
import requests



# custom stuff
from src.Database import database_manager, User, Password, Comments, Listing, Landlord, Rating,Codes, AverageRating
from src.LoginProcessor import PasswordAttempt, get_known_users, update_known_users
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

# queriable by seshid
known_users:dict[str,User] = get_known_users()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("output.ico")

def add_user(username: str, password: str) -> tuple[bool, str]:
    """
    adds user to database\n
    **not cached**

    Uses 6 queries. (2 max if not valid)
    """
    if not username.endswith("@case.edu"):
        return True, "Username must end with @case.edu"

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

    Uses 2 queries.
    """
    data_man.connect_to_database()
    try:
        user_data = data_man.get_user_with_username(username)
        pass_data = data_man.get_pass_from_user(user_data)
        p = PasswordAttempt(user_data.UserID, password, salt=pass_data.Salt)
        return (p.hash == pass_data.Hash) and user_data.Activated
    except TypeError:
        return False

def make_all_listing_data(listings: list[Listing]) -> list[dict]:
    """makes data for all listings

    Args:
        listings (list[Listing]): all listings we want to get data for

    Returns:
        list[dict]: all data for the listing

    Uses 3 queries. (assuming no data is cached)
    """

    # get all data required for this (3 queries)
    users = data_man.get_all_from(User())
    comments = data_man.get_all_from(Comments())
    ar = data_man.get_all_from(AverageRating())

    # compute and compress data

    comments_by_listing:dict[str, list[Comments]] = {}
    for com in comments:
        if com.ListingID in comments_by_listing:
            comments_by_listing[com.ListingID].append(com)
            continue
        comments_by_listing[com.ListingID] = [com]

    user_by_userid:dict[str, User] = {}
    for usr in users:
        if usr.UserID in user_by_userid:
            continue
        user_by_userid[usr.UserID] = usr

    average_by_listing:dict[str, AverageRating] = {}
    for average in ar:
        if average.ListingID in average_by_listing:
            continue
        average_by_listing[average.ListingID] = average


    users_by_comments:dict[str, list[User]] = {}
    for com in comments:
        if com.UserID in users_by_comments:
            users_by_comments[com.UserID].append(user_by_userid[com.UserID])
            continue
        try:
            users_by_comments[com.UserID] = [user_by_userid[com.UserID]]
        except:
            continue


    listing_data = []
    for listing in listings:
        # check for listing in chache
        try:
            if f"listing_{listing.ListingID}" in cache_man.all_refrences:
                cache_data = cache_man.get_cache(f"listing_{listing.ListingID}")
                if cache_data.cache_max_age > datetime.now():
                    # use cached data
                    raw_data:dict = cache_data.cache_data
                    meta_listing:dict = raw_data["meta_listing"]
                    comments_with_users:list = raw_data["comments"]
                    listing_data.append({
                        "listing": meta_listing,
                        "comments": comments_with_users
                    })
                    continue
        except:
            pass

        # meta listing creation
        meta_listing = listing.as_dict()
        try:
            comments = comments_by_listing[listing.ListingID]
        except:
            comments = []
        ar = average_by_listing[listing.ListingID]
        
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
                    "CreatedAt": created_str,
                    "Tags": c.Tags if c.Tags else []
                })
            except TypeError as e:
                print(f"user failed: {e}")
                comments_with_users.append({
                    "Content": c.Content,
                    "Username": "Unknown",
                    "CreatedAt": "",
                    "Tags": c.Tags if c.Tags else []
                })

        # pack into cached data
        data = {"meta_listing":meta_listing,"comments":comments_with_users}
        cache_man.add_to_cache(data,f"listing_{listing.ListingID}")
        listing_data.append({
            "listing": meta_listing,
            "comments": comments_with_users
        })
    return listing_data
    

def make_specific_listing_data(listing: Listing) -> tuple[dict[Any, Any], list[Any]]:
    """Make the data for any one specific listing

    Args:
        listing (Listing): the listing you need data for

    Returns:
        tuple[dict[Any, Any], list[Any]]: the full data output containing a lot of stuff

    Uses 3 queries.
    """
    # meta listing creation
    meta_listing = listing.as_dict()
    comments = data_man.get_comments_from_listing(listing)
    ar = data_man.get_average_rating_from_listing(listing)

    users = data_man.get_all_from(User())
    user_by_userid:dict[str, User] = {}
    for usr in users:
        if usr.UserID in user_by_userid:
            continue
        user_by_userid[usr.UserID] = usr

    
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
            user = user_by_userid[c.UserID]
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
                "CreatedAt": created_str,
                "Tags": c.Tags if c.Tags else []
            })
        except TypeError as e:
            print(f"user failed: {e}")
            comments_with_users.append({
                "Content": c.Content,
                "Username": "Unknown",
                "CreatedAt": "",
                "Tags": c.Tags if c.Tags else []
            })
    return (meta_listing,comments_with_users)

@app.get("/")
def index(request: Request):
    seshid = request.cookies.get("session_id")
    username = "Guest"
    if seshid in known_users:
        username = known_users[seshid].Username
    data_man.connect_to_database()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": (username),
        "title": "Home",
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
    data_man.connect_to_database()
    if verify_login(username, password):
        # real user, make seshid and log as known
        seshid = secrets.token_hex(16) # massive sesh id for security
        known_users[seshid] = data_man.get_user_with_username(username)
        # injecty into webpage
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="session_id", value=seshid, max_age=86400, httponly=True, samesite="lax") # max age 1 day
        update_known_users(known_users,cache_man)
        usr = data_man.get_user_with_username(username)
        if usr.ismod:
            response.set_cookie(key="modkey", value=usr.UserID.encode('utf-8').hex())
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/dashboard")
def dashboard(request: Request):
    seshid = request.cookies.get("session_id")
    hasmodkey = request.cookies.get("modkey") != None
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    username = known_users[seshid].Username
    return templates.TemplateResponse("dashboard.html", {"request": request, "name": username, "hasmodkey": hasmodkey})

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/")
    seshid = request.cookies.get("session_id")
    if seshid in known_users:
        del known_users[seshid]
    response.delete_cookie("session_id")
    return response

@app.get("/comment")
def comment(request: Request):
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    username = known_users[seshid].Username
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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    username = known_users[seshid].Username
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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
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
    # average rating dosnt exist yet, make it
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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    data_man.connect_to_database()

    listings:list[Listing] = data_man.get_all_from(Listing())
    listing_data = make_all_listing_data(listings) # has built in cach checking and renewing

    return templates.TemplateResponse(
        "listings.html",
        {"request": request, "listings": listing_data, "name": "All Listings"}
    )

@app.get("/compare")
def compare(request: Request):
    data_man.connect_to_database()
    listings: list[Listing] = data_man.get_all_from(Listing())
    listing_data = []
    for listing in listings:
        ratings = data_man.get_ratings_from_listing(listing)
        count = len(ratings)
        avg = round(sum(r.Rating for r in ratings) / count, 2) if count > 0 else 0
        listing_data.append({
            "listing": listing.as_dict(),  # ← was just `listing` (not JSON serializable)
            "avg_rating": avg,
            "review_count": count
        })
    return templates.TemplateResponse("compare.html", {
        "request": request,
        "listings": listing_data
    })

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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    user = known_users[seshid]
    data_man.connect_to_database()

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

    return RedirectResponse(url=f"/listing/{listing_id}", status_code=303)


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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    user = known_users[seshid]
    
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

    now_utc = datetime.now(timezone.utc).isoformat()  # store timestamp in UTC

    new_comment = Comments(
        CommentId=secrets.token_hex(8),
        ConnectedCommentID="",
        ListingID=listing_id,
        UserID=user.UserID,
        Content=comment,
        CreatedAt=now_utc,
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

    return RedirectResponse(url=f"/listing/{listing_id}", status_code=303)

@app.get("/listing/{listingid}")
def view_one_listing(request: Request, listingid: str):
    """
    views one listing \n
    **Is cached**
    """
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
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
    seshid = request.cookies.get("session_id")
    if seshid not in known_users:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in to access the dashboard.", "target_url": "/"}
        )
    data_man.connect_to_database()
    listings = [listdict.as_dict() for listdict in data_man.get_all_from(Listing())]
    return templates.TemplateResponse(
        "listing_map.html",
        {
            "request": request,
            "listings": listings
        }
    )

@app.get("/mod_page")
def view_mod_page(request: Request):
    # to be replaced after merge
    username = request.cookies.get("username")
    if not username:
        return templates.TemplateResponse(
            "redirect.html",
            {"request": request, "message": "You must log in.", "target_url": "/login"}
        )
    if request.cookies.get("modkey") != None:
        data_man.connect_to_database()
        user = data_man.get_user_with_username(username)
        if user.UserID.encode('utf-8').hex() == request.cookies.get("modkey"):
            return templates.TemplateResponse(
                "mod_page.html",
                {
                    "request": request
                }
            )
        print(f"invalid mod key, correct key is {user.UserID.encode('utf-8').hex()}")
    return RedirectResponse(url="/dashboard")
@app.post("/mod_page")
def post_mod_page_search(
    request: Request,
    search_type:    str = Form(...),
    get_orphaned:  bool = Form(False),
    uid_search:     str = Form(""),
    content_search: str = Form(""),
    DELETE: bool = Form(False),
    ISPUT: bool = Form(False),
    u_uid: str = Form(None),
    u_usn: str = Form(None),
    u_eml: str = Form(None),
    u_flg: str = Form(None),
    c_cid: str = Form(None),
    l_lid: str = Form(None),
    l_lld: str = Form(None),
    l_adr: str = Form(None),
    l_dsc: str = Form(None),
    l_lat: float = Form(None),
    l_lon: float = Form(None),
    l_bed: int = Form(None),
    l_bat: int = Form(None),
    l_sft: int = Form(None),
    l_rnt: float = Form(None),

):
    # to be replaced after merge
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/dashboard")
    if request.cookies.get("modkey") != None:
        data_man.connect_to_database()
        user = data_man.get_user_with_username(username)
        if user.UserID.encode('utf-8').hex() == request.cookies.get("modkey"):
            if ISPUT:
                print(DELETE)
                if not DELETE:
                    match search_type:
                        case "Users":
                            data_man.update_object(User(UserID=u_uid,Username=u_usn,Email=u_eml,flag=u_flg))
                        case "Listings":
                            data_man.update_object(Listing(
                                ListingID=l_lid,
                                LLID=l_lld,
                                Address=l_adr,
                                Description=l_dsc,
                                CoordinateLat=l_lat,
                                CoordinateLong=l_lon,
                                Baths=l_bat,
                                Beds=l_bed,
                                Price=l_rnt,
                                SquareFootage=l_sft
                            ))
                else:
                    match search_type:
                        case "Users":
                            if u_uid:
                                data_man.recursive_deletion(User(UserID=u_uid))
                        case "Comments":
                            if c_cid:
                                data_man.recursive_deletion(Comments(CommentId=c_cid))
                        case "Listings":
                            if l_lid:
                                data_man.recursive_deletion(Listing(ListingID=l_lid))
                            
            response = None
            match search_type:
                case "Users":
                    if uid_search == "":
                        if not get_orphaned:
                            response = data_man.get_all_from(User())
                        else:
                            response = data_man.find_orphend_data(User())
                    else:
                        response = data_man.get_user_with_username(uid_search)
                case "Comments":
                    if uid_search == "":
                        if not get_orphaned:
                            response = data_man.get_all_from(Comments())
                        else:
                            response = data_man.find_orphend_data(Comments())
                    else:
                        response = data_man.get_comments_from_user(User(UserID=uid_search))
                case "Listings":
                    response = data_man.get_all_from(Listing())
                case "Ratings":
                    if uid_search == "":
                        if not get_orphaned:
                            response = data_man.get_all_from(Rating())
                        else:
                            response = data_man.find_orphend_data(Rating())
                    else:
                        response = data_man.get_ratings_from_user(data_man.get_object_by_id(uid_search, User()))
                        print(data_man.get_object_by_id(uid_search, User()))
                case _:
                    return templates.TemplateResponse(
                    "mod_page.html",
                    {
                        "request": request,
                    }
                )
            # End switch statement
            
            return templates.TemplateResponse(
                "mod_page.html",
                {
                    "request": request,
                    "content_type": search_type,
                    "content": response
                }
            )
    return RedirectResponse(url="/dashboard")
  
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
