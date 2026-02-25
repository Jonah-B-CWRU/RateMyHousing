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
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Comments:
        return Comments(
            dict["CommentId"],
            dict["ConnectedCommentID"],
            dict["ListingID"],
            dict["UserID"],
            dict["Content"],
        )

@dataclass
class Landlord:
    LLID: str = ""
    Name: str = ""
    Email: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Landlord:
        return Landlord(
            dict["LLID"],
            dict["Name"],
            dict["Email"],
        )

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
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Listing:
        return Listing(
            dict["ListingID"],
            dict["LLID"],
            dict["Address"],
            dict["Beds"],
            dict["Baths"],
            dict["SquareFootage"],
            dict["Price"],
            dict["Description"],
        )

@dataclass
class Rating:
    RatingID: str = ""
    UserID: str = ""
    ListingID: str = ""
    Rating: int = 0
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Rating:
        return Rating(
            dict["RatingID"],
            dict["UserID"],
            dict["ListingID"],
            dict["Rating"]
        )

@dataclass
class Password:
    Hash: str = ""
    Salt: str = ""
    UserID: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Password:
        return Password(
            dict["Hash"],
            dict["Salt"],
            dict["UserID"],
        )
    
@dataclass
class User:
    UserID: str = ""
    Username: str = ""
    ConnectedLL: str = ""
    Email: str = ""
    ismod:bool = False
    Activated:bool = False
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> User:
        return User(
            dict["UserID"],
            dict["Username"],
            dict["ConnectedLL"],
            dict["Email"],
            dict["ismod"],
            dict["Activated"],
        )

@dataclass
class Codes:
    UserID: str = ""
    Code: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> Codes:
        return Codes(
            dict["UserID"],
            dict["Code"],
        )

class database_manager:
    connected: bool = False
    fire_store: FirestoreClient

    # Connect to database
    def connect_to_database(self):
        if not self.connected:
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
    
    def get_object_by_id(self, id:str, object_type:User|Rating|Landlord|Password|Comments|Listing) -> User|Rating|Landlord|Password|Comments|Listing:
        """
        Docstring for get_object_by_id
        
        :param self: data manager
        :param id: ID filtering for
        :type id: id
        :param object_type: the type of object we are looking for
        :type object_type: User | Rating | Landlord | Password | Comments | Listing
        :return: the object with the id
        :rtype: User | Rating | Landlord | Password | Comments | Listing
        """
        
        if self.connected:
            match object_type:
                case User():
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        user:dict[str, Any]  = documents[0].to_dict() # type: ignore
                        return User.from_dict(user)
                    raise TypeError(f"No one User with UserID: {id}, there is {len(documents)} of them")
                case Password():
                    collection = self.fire_store.collection("Passwords")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        p:dict[str, Any] = documents[0].to_dict() # type: ignore
                        return Password.from_dict(p)
                    raise TypeError(f"No one Password with UserID: {id}, there is {len(documents)} of them")
                case Comments():
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("CommentID", "==", id).get()
                    if len(documents) == 1:
                        c:dict[str, Any]  = documents[0].to_dict() # type: ignore
                        return Comments.from_dict(c)
                    raise TypeError(f"No one Comment with CommentId: {id}, there is {len(documents)} of them")
                case Landlord():
                    collection = self.fire_store.collection("Landlord")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        l:dict[str, Any]  = documents[0].to_dict() # type: ignore
                        return Landlord.from_dict(l)
                    raise TypeError(f"No one Landlord with LLID: {id}, there is {len(documents)} of them")
                case Listing():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        l:dict[str, Any]  = documents[0].to_dict() # type: ignore
                        return Listing.from_dict(l)
                    raise TypeError(f"No one Listing with ListingID: {id}, there is {len(documents)} of them")
                case Rating():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("RatingID", "==", id).get()
                    if len(documents) == 1:
                        r:dict[str, Any]  = documents[0].to_dict() # type: ignore
                        return Rating.from_dict(r)
                    raise TypeError(f"No one Rating with RatingID: {id}, there is {len(documents)} of them")
        raise IOError("Not Connected to Database")

    def recursive_deletion(self, deleted_object:User|Rating|Landlord|Password|Comments|Listing) -> bool:
        # recursive so it actually implements castcading removal.
        if self.connected:
            match deleted_object:
                case User():
                    # remove main object
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", deleted_object.UserID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                        return False

                    # get connected items

                        # passwords
                    password = self.get_pass_from_user(deleted_object)
                    self.recursive_deletion(password)

                        # comments
                    comments = self.get_comments_from_user(deleted_object)
                    for c in comments:
                        self.recursive_deletion(c)

                        # ratings
                    ratings = self.get_ratings_from_user(deleted_object)
                    for r in ratings:
                        self.recursive_deletion(r)
                    return True
                case Password():
                    # remove password and leave.
                    collection = self.fire_store.collection("Password")
                    documents = collection.where("UserID", "==", deleted_object.UserID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True               
                case Rating():
                    # remove rating and leave.
                    collection = self.fire_store.collection("Rating")
                    documents = collection.where("RatingID", "==", deleted_object.RatingID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True                
                case Landlord():
                    # remove main object
                    collection = self.fire_store.collection("Landlords")
                    documents = collection.where("LLID", "==", deleted_object.LLID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False

                    # get connected items
                        # Users
                    users = self.get_connected_users_with_landlord(deleted_object)
                    for u in users:
                        self.recursive_deletion(u)
                    
                        # listings
                    listings = self.get_connected_listings_with_landlord(deleted_object)
                    for l in listings:
                        self.recursive_deletion(l)
                    return True
                case Comments():
                    # remove comment and leave.
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("CommentId", "==", deleted_object.CommentId).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True
                case Listing():
                    # remove main object
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("ListingID", "==", deleted_object.ListingID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False

                    # get connected items
                        # comments
                    comments = self.get_comments_from_listing(deleted_object)
                    for c in comments:
                        self.recursive_deletion(c)

                        # ratings
                    ratings = self.get_ratings_from_listing(deleted_object)
                    for r in ratings:
                        self.recursive_deletion(r)
                    return True
                case _:
                    raise TypeError(f"Id_source Not Valid Type: {Id_type}, {type(Id_type)}")
        raise IOError("Not Connected to Database")
    
    def get_all_from(self, data_class:User|Rating|Landlord|Password|Comments|Listing) -> list[Comments|Landlord|Listing|Password|Rating|User]:
        """
        Docstring for get_all_from
        
        :param self: data manager
        :param data_class: the data type you want to get
        :type data_class: User | Rating | Landlord | Password | Comments | Listing
        :return: all of the table from the data type you asked for
        :rtype: list[Comments|Landlord|Listing|Password|Rating|User]
        """
        collection = ""
        match data_class:
            case User():
                collection = "Users"
            case Rating():
                collection = "Rating"
            case Landlord():
                collection = "Landlords"
            case Password():
                collection = "Passwords"
            case Comments():
                collection = "Comments"
            case Listing():
                collection = "Listing"

        if self.connected:
            datalist = self._get_data(collection)
            return [data_class.from_dict(i) for i in datalist]
        else:
            raise IOError("Not Connected")

    def add_object(self,object:User|Rating|Landlord|Password|Comments|Listing):
        collection = ""
        match object:
            case User():
                collection = "Users"
            case Rating():
                collection = "Rating"
            case Landlord():
                collection = "Landlords"
            case Password():
                collection = "Passwords"
            case Comments():
                collection = "Comments"
            case Listing():
                collection = "Listing"
        if self.connected:
            result = self._push_data(object.as_dict(),collection)
        else:
            raise IOError("Not Connected")

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
    # user <-> comments (many)
    def get_user_with_username(self, username:str) -> User:
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = self._unwrap_query(query)
            if len(user) == 1:
                user = user[0]
                return User.from_dict(user)
            else:
                raise TypeError(f"no user with the username: {username}")
        raise IOError("Not Connected to Database")

    def get_pass_from_user(self, user:User) -> Password:
        if self.connected:
            password_list = self._get_document_using_id("Passwords",User(),user.UserID)
            if len(password_list) == 1:
                p = password_list[0]
                return Password.from_dict(p)
            else:
                raise TypeError(f"no password with userid: {user.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_landlord_from_user(self, user:User) -> Landlord:
        if self.connected:
            if user.ConnectedLL ==  "":
                raise TypeError(f"User has no LLID")
            Landlord_list = self._get_document_using_id("Lanloards", Landlord(),user.ConnectedLL)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord.from_dict(l)
            else:
                raise TypeError(f"no Lanloard with LLID: {user.ConnectedLL}")
        raise IOError("Not Connected to Database")

    def get_ratings_from_user(self, user:User) -> list[Rating]:
        if self.connected:
            ratings = self._get_document_using_id("Rating", User(),user.UserID)
            return [Rating.from_dict(r) for r in ratings]
        raise IOError("Not Connected to Database")
    
    def get_comments_from_user(self, user:User) -> list[Comments]:
        if self.connected:
            coms = self._get_document_using_id("Comments", User(),user.UserID)
            return [Comments.from_dict(c) for c in coms]
        raise IOError("Not Connected to Database")
    
    # rating relationships
    # Rating <-> user
    # Rating <-> Listing
    def get_user_from_rating(self,rating:Rating) -> User:
        if self.connected:
            users = self._get_document_using_id("User",User(),rating.UserID)
            if len(users) == 1:
                u = users[0]
                return User.from_dict(u)
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
    # comment <-> user
    # comment -> comment
    # comment <-> listing
    def get_user_from_comments(self,comment:Comments) -> User:
        if self.connected:
            users = self._get_document_using_id("User",User(),comment.UserID)
            if len(users) == 1:
                u = users[0]
                return User.from_dict(u)
            else:
                raise TypeError(f"no username with userid: {comment.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_comments_from_comments(self,comment:Comments) -> Comments:
        if self.connected:
            com = self._get_document_using_id("Comments",Comments(),comment.ConnectedCommentID)
            if len(com) == 1:
                c = com[0]
                return Comments.from_dict(c)
            else:
                raise TypeError(f"no comment with comment: {comment.ConnectedCommentID}")
        raise IOError("Not Connected to Database")
    
    def get_listing_from_comments(self,comment:Comments) -> Listing:
        if self.connected:
            listings = self._get_document_using_id("Listing",Listing(),comment.ListingID)
            if len(listings) == 1:
                l = listings[0]
                return Listing.from_dict(l)
            else:
                raise TypeError(f"no listing with ListingID: {comment.ListingID}")
        raise IOError("Not Connected to Database")
    

    # Listing relationships
    # listing -> landlord
    # listing <-> Rating (many)
    # listing <-> Comments (many)
    def get_landlord_from_Listing(self, listing:Listing) -> Landlord:
        if self.connected:
            Landlord_list = self._get_document_using_id("Lanloards", Landlord(),listing.LLID)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord.from_dict(l)
            else:
                raise TypeError(f"no Lanloard with LLID: {listing.LLID}")
        raise IOError("Not Connected to Database")
    
    def get_ratings_from_listing(self, listing:Listing) -> list[Rating]:
        if self.connected:
            ratings = self._get_document_using_id("Rating", Listing(),listing.ListingID)
            return [Rating.from_dict(r) for r in ratings]
        raise IOError("Not Connected to Database")
    
    def get_comments_from_listing(self, listing:Listing) -> list[Comments]:
        if self.connected:
            coms = self._get_document_using_id("Comments", Listing(),listing.ListingID)
            return [Comments.from_dict(c) for c in coms]
        raise IOError("Not Connected to Database")
    
    # landlord rlationships
    # Landlord <-> User (many)
    # Landlord <-> Listing (many)
    def get_connected_users_with_landlord(self, landlord:Landlord) -> list[User]:
        if self.connected:
            users = self._get_document_using_id("User", Landlord(),landlord.LLID)
            return [User.from_dict(u) for u in users]
        raise IOError("Not Connected to Database")
    
    def get_connected_listings_with_landlord(self, landlord:Landlord) -> list[Listing]:
        if self.connected:
            listings = self._get_document_using_id("Listing", Landlord(),landlord.LLID)
            return [Listing.from_dict(l) for l in listings]
        raise IOError("Not Connected to Database")