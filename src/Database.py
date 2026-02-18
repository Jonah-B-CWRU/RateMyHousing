from typing import Any
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.query import Query
from dataclasses import dataclass, asdict
from google.protobuf import timestamp_pb2
import firebase_admin

# all dataclasses's for easy use
@dataclass
class Comments:
    CommentId: str = ""
    ConnectedCommentID: str = ""
    ListingID: str = ""
    UserID:str = ""
    Content: str = ""
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

    # Connect to database
    def connect_to_database(self):
        if not self.connected:
            data:dict[str,str] = {}
            cred = credentials.Certificate("src/Secrets.json")
            fire_app = firebase_admin.initialize_app(cred)
            self.connected = True
            self.fire_store = firestore.client(fire_app)
    
    def _get_data(self, col:str) -> list[dict[str,Any]]:
        collection = self.fire_store.collection(col)
        query = collection.get()
        total_data = []
        for doc in query:
            data = doc.to_dict()
            total_data.append(data)
        return total_data
    
    def _push_data(self, data:dict,col:str) -> tuple[timestamp_pb2.Timestamp,DocumentReference]: # type: ignore
        collection = self.fire_store.collection(col)
        return collection.add(data)
    
    # users
    def get_users(self) -> list[dict[str,Any]]:
        if self.connected:
            return self._get_data("Users")
        else:
            raise IOError("Not Connected")
    
    def add_user(self, user:User):
        if self.connected:
            result = self._push_data(user.as_dict(),"Users")
            print(result)

    # Passwords
    def get_passwords(self) -> list[dict[str,Any]]:
        if self.connected:
            return self._get_data("Passwords")
        else:
            raise IOError("Not Connected")
    
    def add_passwords(self, password:Password):
        if self.connected:
            result = self._push_data(password.as_dict(),"Passwords")
            print(result)
	
    # Comments
    def get_comments(self):
        if self.connected:
            return self._get_data("Comments")
        else:
            raise IOError("Not Connected")

    def add_comment(self, comment:Comments):
        if self.connected:
            result = self._push_data(comment.as_dict(),"Comments")

    # Listing
    def get_listings(self):
        if self.connected:
            return self._get_data("Listing")
        else:
            raise IOError("Not Connected")
    
    def get_all_listings(self) -> list[Listing]:
        if self.connected:
            collection = self.fire_store.collection("Listing")
            docs = collection.stream()

            out: list[Listing] = []
            for doc in docs:
                l = doc.to_dict()
                out.append(
                    Listing(
                        l.get("ListingID", ""),
                        l.get("LLID", ""),
                        l.get("Address", ""),
                        l.get("Beds", 0),
                        l.get("Baths", 0),
                        l.get("SquareFootage", 0),
                        l.get("Price", 0.0),
                        l.get("Description", "")
                    )
                )

            return out

        raise IOError("Not Connected to Database")


    def add_listing(self, listing:Listing):
        if self.connected:
            result = self._push_data(listing.as_dict(),"Listing")

    # Landloard
    def get_landlords(self):
        if self.connected:
            return self._get_data("Landlord")
        else:
            raise IOError("Not Connected")

    def add_landlord(self, landlord:Landlord):
        if self.connected:
            result = self._push_data(landlord.as_dict(),"Landlord")

    # Rating
    def get_ratings(self):
        if self.connected:
            return self._get_data("Rating")
        else:
            raise IOError("Not Connected")

    def add_rating(self, rating:Rating):
        if self.connected:
            result = self._push_data(rating.as_dict(),"Rating")


    # relating stuff
    def _unwrap_query(self, q:Query) -> list[dict]:
        total_data:list[dict] = []
        for doc in q.get():
            data = doc.to_dict()
            if data != None:
                total_data.append(data)
        return total_data
    
    def _get_document_using_id(self,collection_to_search:str, Id_type:User|Rating|Landlord|Password|Comments|Listing, Id_to_look_for:str)-> list[dict]:
        """
        Searches the specified collection for all documents with the corresponding ID.
        
        Parameters:
            collection_to_search (str): The name of the collection to search within.
            Id_type (User|Rating|Landlord|Password|Comments|Listing): The document containing the ID to search for.
            Id_to_look_for (str): exact text of cid to look for

        Returns:
            list: A list of documents that match the specified ID.
        """
        if self.connected:
            collection = self.fire_store.collection(collection_to_search)
            match Id_type:
                case User():
                    query = collection.where("UserID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Password():
                    query = collection.where("UserID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Rating():
                    query = collection.where("RatingID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Landlord():
                    query = collection.where("LLID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Comments():
                    query = collection.where("CommentId", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Listing():
                    query = collection.where("ListingID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case _:
                    raise TypeError(f"Id_source Not Valid Type: {Id_type}, {type(Id_type)}")
        raise IOError("Not Connected to Database")
    
    def check_for_username(self, username:str) -> bool:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = self._unwrap_query(query)
            if len(user) >= 1:
                return True
            else:
                return False
        raise IOError("Not Connected to Database")
   
    def check_for_email(self, email:str) -> bool:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Email","==",email)
            user = self._unwrap_query(query)
            if len(user) >= 1:
                return True
            else:
                return False
        raise IOError("Not Connected to Database")


    # User relations
    # username -> user
    # user -> password
    # User <-> lanloard
    # user <-> rating (many)
    def get_user_with_username(self, username:str) -> User:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = self._unwrap_query(query)
            if len(user) == 1:
                user = user[0]
                return User(user["UserID"],user["Username"],user["ConnectedLL"],user["Email"])
            else:
                raise TypeError(f"no user with the username: {username}")
        raise IOError("Not Connected to Database")

    def get_pass_from_user(self, user:User) -> Password:
        if self.connected:
            password_list = self._get_document_using_id("Passwords",User(),user.UserID)
            if len(password_list) == 1:
                p = password_list[0]
                return Password(p["Hash"],p["Salt"],p["UserID"])
            else:
                raise TypeError(f"no password with userid: {user.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_lanloard_from_user(self, user:User) -> Landlord:
        if self.connected:
            Landlord_list = self._get_document_using_id("Lanloards", Landlord(),user.ConnectedLL)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord(l["LLID"],l["Name"],l["Email"])
            else:
                raise TypeError(f"no Lanloard with LLID: {user.ConnectedLL}")
        raise IOError("Not Connected to Database")

    def get_ratings_from_user(self, user:User) -> list[Rating]:
        if self.connected:
            ratings = self._get_document_using_id("Rating", User(),user.UserID)
            out:list[Rating] = []
            for r in ratings:
                out.append(Rating(r["RatingID"],r["UserID"],r["ListingID"],r["Rating"]))
            return out
        raise IOError("Not Connected to Database")
    
    # rating relationships
    # Rating <-> user
    # Rating <-> Listing
    def get_user_from_rating(self,rating:Rating) -> User:
        if self.connected:
            users = self._get_document_using_id("User",User(),rating.UserID)
            if len(users) == 1:
                u = users[0]
                return User(u["UserID"],u["Username"],u["ConnectedLL"],u["Email"])
            else:
                raise TypeError(f"no username with userid: {rating.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_listing_from_rating(self,rating:Rating) -> Listing:
        if self.connected:
            listings = self._get_document_using_id("Listing",Listing(),rating.ListingID)
            if len(listings) == 1:
                l = listings[0]
                return Listing(l["ListingID"],l["LLID"],l["ListingLocation"])
            else:
                raise TypeError(f"no listing with ListingID: {rating.ListingID}")
        raise IOError("Not Connected to Database")
    
    # comments relationships
    # comment -> user
    # comment -> comment
    # comment <-> listing
    def get_user_from_comments(self,comment:Comments) -> User:
        if self.connected:
            users = self._get_document_using_id("User",User(),comment.UserID)
            if len(users) == 1:
                u = users[0]
                return User(u["UserID"],u["Username"],u["ConnectedLL"],u["Email"])
            else:
                raise TypeError(f"no username with userid: {comment.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_comments_from_comments(self,comment:Comments) -> Comments:
        if self.connected:
            com = self._get_document_using_id("Comments",Comments(),comment.ConnectedCommentID)
            if len(com) == 1:
                c = com[0]
                return Comments(c["CommentId"],c["ConnectedCommentID"],c["ListingID"],c["UserID"],c["Content"])
            else:
                raise TypeError(f"no comment with comment: {comment.ConnectedCommentID}")
        raise IOError("Not Connected to Database")
    
    def get_listing_from_comments(self,comment:Comments) -> Listing:
        if self.connected:
            listings = self._get_document_using_id("Listing",Listing(),comment.ListingID)
            if len(listings) == 1:
                l = listings[0]
                return Listing(l["ListingID"],l["LLID"],l["ListingLocation"])
            else:
                raise TypeError(f"no listing with ListingID: {comment.ListingID}")
        raise IOError("Not Connected to Database")
    

    # Listing relationships
    # listing -> landlord
    # listing <-> Rating (many)
    # listing <-> Comments (many)
    def get_lanloard_from_Listing(self, listing:Listing) -> Landlord:
        if self.connected:
            Landlord_list = self._get_document_using_id("Lanloards", Landlord(),listing.LLID)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord(l["LLID"],l["Name"],l["Email"])
            else:
                raise TypeError(f"no Lanloard with LLID: {listing.LLID}")
        raise IOError("Not Connected to Database")
    
    def get_ratings_from_listing(self, listing:Listing) -> list[Rating]:
        if self.connected:
            ratings = self._get_document_using_id("Rating", Listing(),listing.ListingID)
            out:list[Rating] = []
            for r in ratings:
                out.append(Rating(r["RatingID"],r["UserID"],r["ListingID"],r["Rating"]))
            return out
        raise IOError("Not Connected to Database")
    
    def get_comments_from_listing(self, listing:Comments) -> list[Comments]:
        if self.connected:
            coms = self._get_document_using_id("Comments", Listing(),listing.ListingID)
            out:list[Comments] = []
            for c in coms:
                out.append(Comments(c["CommentId"],c["ConnectedCommentID"],c["ListingID"],c["UserID"],c["Content"]))
            return out
        raise IOError("Not Connected to Database")
    
    # landlord rlationships
    # Landlord <-> User (many)
    # Landlord <-> Listing (many)
    def get_connected_users_with_landlord(self, landlord:Landlord) -> list[User]:
        if self.connected:
            users = self._get_document_using_id("User", Landlord(),landlord.LLID)
            out:list[User] = []
            for u in users:
                out.append(User(u["UserID"],u["Username"],u["ConnectedLL"],u["Email"]))
            return out
        raise IOError("Not Connected to Database")
    
    def get_connected_listings_with_landlord(self, landlord:Landlord) -> list[Listing]:
        if self.connected:
            listings = self._get_document_using_id("Listing", Landlord(),landlord.LLID)
            out:list[Listing] = []
            for l in listings:
                out.append(Listing(l["ListingID"],l["LLID"],l["ListingLocation"]))
            return out
        raise IOError("Not Connected to Database")