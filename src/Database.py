from typing import Any
from firebase_admin import firestore, credentials # type: ignore
from google.cloud.firestore_v1.client import Client as FirestoreClient # type: ignore
from google.cloud.firestore_v1.document import DocumentReference # type: ignore
from google.cloud.firestore_v1.query import Query # type: ignore
from dataclasses import dataclass, asdict
from google.protobuf import timestamp_pb2 # type: ignore
import firebase_admin # type: ignore
import secrets

@dataclass
class Comments:
    CommentId: str = ""
    ConnectedCommentID: str = ""
    ListingID: str = ""
    UserID:str = ""
    Content: str = ""
    CreatedAt: str = ""
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Landlord:
    LLID: str = ""
    Name: str = ""
    Email: str = ""
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Listing:
    ListingID: str = ""
    LLID: str = ""
    Address: str = ""
    Beds: int = 0
    Baths: int = 0
    SquareFootage: int = 0
    Price: float = 0.0
    Description: str = ""
    CreatedAt: str = ""
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Rating:
    RatingID: str = ""
    UserID: str = ""
    ListingID: str = ""
    Rating: int = 0
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Password:
    Hash: str = ""
    Salt: str = ""
    UserID: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    
@dataclass
class User:
    UserID: str = ""
    Username: str = ""
    ConnectedLL: str = ""
    Email: str = ""
    def as_dict(self) -> dict:
        return asdict(self)

class database_manager:
    connected: bool = False
    fire_store: FirestoreClient

    def connect_to_database(self):
        if not self.connected:
            cred = credentials.Certificate("src/Secrets.json")
            firebase_admin.initialize_app(cred)
            self.connected = True
            self.fire_store = firestore.client()
    
    def _get_data(self, col:str) -> list[dict[str,Any]]:
        collection = self.fire_store.collection(col)
        query = collection.get()
        total_data = [doc.to_dict() for doc in query]
        return total_data
    
    def _push_data(self, data:dict,col:str) -> tuple[timestamp_pb2.Timestamp,DocumentReference]:
        collection = self.fire_store.collection(col)
        return collection.add(data)

    def get_users(self) -> list[dict[str,Any]]:
        if self.connected:
            return self._get_data("Users")
        else:
            raise IOError("Not Connected")
    
    def add_user(self, user:User):
        if self.connected:
            self._push_data(user.as_dict(),"Users")

    def get_passwords(self) -> list[dict[str,Any]]:
        if self.connected:
            return self._get_data("Passwords")
        else:
            raise IOError("Not Connected")
    
    def add_passwords(self, password:Password):
        if self.connected:
            self._push_data(password.as_dict(),"Passwords")
	
    def get_comments(self):
        if self.connected:
            return self._get_data("Comments")
        else:
            raise IOError("Not Connected")

    def add_comment(self, comment:Comments):
        if self.connected:
            self._push_data(comment.as_dict(),"Comments")

    def get_listings(self):
        if self.connected:
            return self._get_data("Listing")
        else:
            raise IOError("Not Connected")
    
    def get_all_listings(self) -> list[Listing]:
        if self.connected:
            collection = self.fire_store.collection("Listing")
            docs = collection.stream()
            out = []
            for doc in docs:
                l = doc.to_dict()
                out.append(Listing(
                    l.get("ListingID", ""),
                    l.get("LLID", ""),
                    l.get("Address", ""),
                    l.get("Beds", 0),
                    l.get("Baths", 0),
                    l.get("SquareFootage", 0),
                    l.get("Price", 0.0),
                    l.get("Description", ""),
                    l.get("CreatedAt", "")
                ))
            return out
        raise IOError("Not Connected to Database")

    def add_listing(self, listing:Listing):
        if self.connected:
            self._push_data(listing.as_dict(),"Listing")

    def get_landlords(self):
        if self.connected:
            return self._get_data("Landlord")
        else:
            raise IOError("Not Connected")

    def add_landlord(self, landlord:Landlord):
        if self.connected:
            self._push_data(landlord.as_dict(),"Landlord")

    def get_ratings(self):
        if self.connected:
            return self._get_data("Rating")
        else:
            raise IOError("Not Connected")

    def add_rating(self, rating:Rating):
        if self.connected:
            self._push_data(rating.as_dict(),"Rating")

    def check_for_username(self, username:str) -> bool:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = [doc.to_dict() for doc in query.get()]
            return len(user) >= 1
        raise IOError("Not Connected to Database")
   
    def check_for_email(self, email:str) -> bool:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Email","==",email)
            user = [doc.to_dict() for doc in query.get()]
            return len(user) >= 1
        raise IOError("Not Connected to Database")

    def get_user_with_username(self, username:str) -> User:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = [doc.to_dict() for doc in query.get()]
            if len(user) == 1:
                u = user[0]
                return User(u["UserID"],u["Username"],u["ConnectedLL"],u["Email"])
            else:
                raise TypeError(f"no user with the username: {username}")
        raise IOError("Not Connected to Database")

    def get_pass_from_user(self, user:User) -> Password:
        if self.connected:
            collection = self.fire_store.collection("Passwords")
            query = collection.where("UserID","==",user.UserID)
            passwords = [doc.to_dict() for doc in query.get()]
            if len(passwords) == 1:
                p = passwords[0]
                return Password(p["Hash"],p["Salt"],p["UserID"])
            else:
                raise TypeError(f"no password with userid: {user.UserID}")
        raise IOError("Not Connected to Database")

    def get_ratings_from_listing(self, listing:Listing) -> list[Rating]:
        if self.connected:
            collection = self.fire_store.collection("Rating")
            query = collection.where("ListingID","==",listing.ListingID)
            ratings = [doc.to_dict() for doc in query.get()]
            out = []
            for r in ratings:
                out.append(Rating(r["RatingID"],r["UserID"],r["ListingID"],r["Rating"]))
            return out
        raise IOError("Not Connected to Database")
    
    def get_comments_from_listing(self, listing:Listing) -> list[Comments]:
        if self.connected:
            collection = self.fire_store.collection("Comments")
            query = collection.where("ListingID","==",listing.ListingID)
            comments = [doc.to_dict() for doc in query.get()]
            out = []
            for c in comments:
                out.append(Comments(
                    CommentId=c.get("CommentId", ""),
                    ConnectedCommentID=c.get("ConnectedCommentID", ""),
                    ListingID=c.get("ListingID", ""),
                    UserID=c.get("UserID", ""),
                    Content=c.get("Content", ""),
                    CreatedAt=c.get("CreatedAt", "")
                ))
            return out
        raise IOError("Not Connected to Database")
    def get_user_from_id(self, user_id: str) -> User:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("UserID", "==", user_id)
            users = [doc.to_dict() for doc in query.get()]
            if users:
                u = users[0]
                return User(u["UserID"], u["Username"], u["ConnectedLL"], u["Email"])
        raise TypeError(f"No user with ID: {user_id}")