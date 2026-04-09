from dataclasses import dataclass, asdict, fields,field
from typing import Any, TypeAlias, TypeVar, cast
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference, DocumentSnapshot
from google.cloud.firestore_v1.query import Query
from google.cloud.firestore_v1.query_results import QueryResultsList
from google.cloud.firestore_v1.types.write import WriteResult
from google.cloud.firestore_v1.base_query import FieldFilter
from google.protobuf import timestamp_pb2
from email.mime.text import MIMEText
import firebase_admin
import json  
import smtplib

@dataclass
class Comments:
    CommentId: str = ""
    ConnectedCommentID: str = ""
    ListingID: str = ""
    UserID:str = ""
    Content: str = ""
    CreatedAt: str = ""
    Tags: list[str] = field(default_factory=list)
    def as_dict(self) -> dict:
        data = asdict(self)
        if data["Tags"] is None:
            data["Tags"] = []
        return data
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "Comments":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class Landlord:
    LLID: str = ""
    Name: str = ""
    Email: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "Landlord":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class Listing:
    ListingID: str = ""
    LLID: str = ""
    LLName: str = ""
    LLEmail: str = ""
    Address: str = ""
    Beds: int = 0
    Baths: int = 0
    SquareFootage: int = 0
    Price: float = 0.0
    Description: str = ""
    CreatedAt: str = ""
    CoordinateLat: float = 0.0
    CoordinateLong: float = 0.0
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "Listing":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class Rating:
    RatingID: str = ""
    UserID: str = ""
    ListingID: str = ""
    Rating: int = 0
    #Tags: list[str] = None

    def as_dict(self) -> dict:
        data = asdict(self)
        #if data["Tags"] is None:
        #    data["Tags"] = []
        return data
    @classmethod
    def from_dict(cls,dict: dict[str,Any]) -> "Rating":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class Password:
    Hash: str = ""
    Salt: str = ""
    UserID: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "Password":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)
    
@dataclass
class User:
    UserID: str = ""
    Username: str = ""
    ConnectedLL: str = ""
    Email: str = ""
    ismod:bool = False
    Activated:bool = False
    flag:str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "User":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class Codes:
    UserID: str = ""
    Code: int = 0
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls,dict: dict[str,Any]) -> "Codes":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)

@dataclass
class AverageRating:
    ListingID: str = ""
    AverageRating: float = 0.0
    NumberOfRatings: int = 0
    def as_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "AverageRating":
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)


# super type alias
DataObject: TypeAlias = User | Rating | Landlord | Password | Comments | Listing | Codes | AverageRating

T = TypeVar("T", bound=DataObject)
class database_manager:
    connected: bool = False
    fire_store: FirestoreClient

    def connect_to_database(self):
        """
        Connects to database and sets things up internally.

        Always run before any other commands
        """
        if not self.connected:
            cred = credentials.Certificate("src/Secrets.json")
            firebase_admin.initialize_app(cred)
            self.connected = True
            self.fire_store = firestore.client()
            self.update_all_average_ratings()
    
    # basic data handeling
    def _get_data(self, col:str) -> list[dict[str,Any]]:
        """gets data from database. INTERNAL DO NOT USE UNLESS YOU KNOW WHAT YOU'RE DOING

        Uses 1 query

        Args:
            col (str): What collection to get from

        Returns:
            list[dict[str,Any]]: A list of all object gathered
        """
        collection = self.fire_store.collection(col)
        query = collection.get()
        total_data = []
        for doc in query:
            data = doc.to_dict()
            total_data.append(data)
        return total_data
    
    def _get_raw_data(self,col:str) -> QueryResultsList[DocumentSnapshot]:
        """gets data from database. INTERNAL DO NOT USE UNLESS YOU KNOW WHAT YOU'RE DOING

        Uses 1 query

        Args:
            col (str): What collection to get from

        Returns:
            QueryResultsList[DocumentSnapshot]: a list of all of the raw documents in the collection.          
        """
        collection = self.fire_store.collection(col)
        query = collection.get()
        return query

    
    def _push_data(self, data:dict,col:str) -> tuple[timestamp_pb2.Timestamp,DocumentReference]: # type: ignore
        """Push data to the database. INTERNAL DO NOT USE

        Uses 1 query

        Args:
            data (dict): raw data to push
            col (str): what collection it should go to

        Returns:
            tuple[timestamp_pb2.Timestamp,DocumentReference]: a typle containing when it was pushed and where it was pushed to
        """
        collection = self.fire_store.collection(col)
        return collection.add(data)
    
    def _unwrap_query(self, q:Query) -> list[dict]:
        """Forcefully unwraps a query. INTERNAL DO NOT USE UNLESS YOU KNOW WHAT YOU'RE DOING

        Uses 0 queries

        Args:
            q (Query): any firebase query

        Returns:
            list[dict]: a dictinary list of everything inside that query. can be packed back into types
        """
        total_data:list[dict] = []
        for doc in q.get():
            data = doc.to_dict()
            if data != None:
                total_data.append(data)
        return total_data
    
    def _get_document_using_id(self,collection_to_search:str, Id_type:DataObject, Id_to_look_for:str)-> list[dict]:
        """
        Searches the specified collection for all documents with the corresponding ID.

        Uses 1 query
        
        Parameters:
            collection_to_search (str): The name of the collection to search within.
            Id_type (DataObject): The document containing the ID to search for.
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
                    # unique case: users
                    if collection_to_search == "Users":
                        query = collection.where("ConnectedLL", "==", Id_to_look_for)
                    else:
                        query = collection.where("LLID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Comments():
                    query = collection.where("CommentId", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                    
                case Listing():
                    query = collection.where("ListingID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                
                case Codes():
                    query = collection.where("UserID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                
                case AverageRating():
                    query = collection.where("ListingID", "==", Id_to_look_for)
                    return self._unwrap_query(query)
                case _:
                    raise TypeError(f"Id_source Not Valid Type: {Id_type}, {type(Id_type)}")
        raise IOError("Not Connected to Database")

    # basic object handeling
    def get_object_by_id(self, id:str, object_type:T) -> T:
        """get any one object when given its id and its type

        Uses 1 query

        Args:
            id (str): the id of the requested object
            object_type (T): the type of the requested object

        Raises:
            TypeError: invalid id
            IOError: not connected

        Returns:
            T: full object of the given type
        """
        if self.connected:
            match object_type:
                case User():
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        user  = documents[0].to_dict()
                        if user != None:
                            return cast(T, User.from_dict(user))
                    raise TypeError(f"No one User with UserID: {id}, there is {len(documents)} of them")
                case Password():
                    collection = self.fire_store.collection("Passwords") 
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        p = documents[0].to_dict()
                        if p != None:
                            return cast(T, Password.from_dict(p))
                    raise TypeError(f"No one Password with UserID: {id}, there is {len(documents)} of them")
                case Comments():
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("CommentID", "==", id).get()
                    if len(documents) == 1:
                        c = documents[0].to_dict()
                        if c != None:
                            return cast(T, Comments.from_dict(c))
                    raise TypeError(f"No one Comment with CommentId: {id}, there is {len(documents)} of them")
                case Landlord():
                    collection = self.fire_store.collection("Landlord")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        l  = documents[0].to_dict()
                        if l != None:
                             return cast(T, Landlord.from_dict(l))
                    raise TypeError(f"No one Landlord with LLID: {id}, there is {len(documents)} of them")
                case Listing():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        l  = documents[0].to_dict()
                        if l != None:
                            return cast(T, Listing.from_dict(l))
                    raise TypeError(f"No one Listing with ListingID: {id}, there is {len(documents)} of them")
                case Rating():
                    collection = self.fire_store.collection("Rating")
                    documents = collection.where("RatingID", "==", id).get()
                    if len(documents) == 1:
                        r  = documents[0].to_dict()
                        if r != None:
                            return cast(T, Rating.from_dict(r))
                    raise TypeError(f"No one Rating with RatingID: {id}, there is {len(documents)} of them")
                case Codes():
                    collection = self.fire_store.collection("Codes")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        c  = documents[0].to_dict()
                        if c != None:
                            return cast(T, Codes.from_dict(c))
                    raise TypeError(f"No one Code with UserID: {id}, there is {len(documents)} of them")
                case AverageRating():
                    collection = self.fire_store.collection("AverageRating")
                    documents = collection.where("ListingID", "==", id).get()
                    if len(documents) == 1:
                        ar  = documents[0].to_dict()
                        if ar != None:
                            return cast(T, AverageRating.from_dict(ar))
                    raise TypeError(f"No one AverageRating with ListingID: {id}, there is {len(documents)} of them")
        raise IOError("Not Connected to Database")

    def recursive_deletion(self, deleted_object:DataObject) -> bool:
        """Recursivly removes all objects connected to the deleated object. including the origional object

        Uses 1 query per object deleated.

        Args:
            deleted_object (DataObject): any data object

        Raises:
            TypeError: Invalid data type
            IOError: not connected

        Returns:
            bool: weather deleation was sucessfull or not 
        """
        # recursive so it actually implements castcading removal.
        if self.connected:
            match deleted_object:
                case User():
                    # remove main object
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", deleted_object.UserID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False

                    # get connected items

                        # passwords
                    try:
                        password = self.get_pass_from_user(deleted_object)
                        self.recursive_deletion(password)
                    except:
                        pass

                        # comments
                    try:
                        comments = self.get_comments_from_user(deleted_object)
                        for c in comments:
                            self.recursive_deletion(c)
                    except:
                        pass

                        # ratings
                    try:
                        ratings = self.get_ratings_from_user(deleted_object)
                        for r in ratings:
                            self.recursive_deletion(r)
                    except:
                            pass
                    
                        # codes
                    try:
                        code = self.get_code_from_user(deleted_object)
                        self.recursive_deletion(code)
                    except:
                            pass
                    return True
                case Password():
                    # remove password and leave.
                    collection = self.fire_store.collection("Passwords")
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
                    try:
                        users = self.get_connected_users_with_landlord(deleted_object)
                        for u in users:
                            self.recursive_deletion(u)
                    except:
                            pass
                        # listings
                    try:
                        listings = self.get_connected_listings_with_landlord(deleted_object)
                        for l in listings:
                            self.recursive_deletion(l)
                    except:
                            pass
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
                    try:
                        comments = self.get_comments_from_listing(deleted_object)
                        for c in comments:
                            self.recursive_deletion(c)
                    except:
                            pass
                        # ratings
                    try:
                        ratings = self.get_ratings_from_listing(deleted_object)
                        for r in ratings:
                            self.recursive_deletion(r)
                    except:
                            pass
                        # rating average
                    #average = 
                    return True
                case Codes():
                    # remove code and leave.
                    collection = self.fire_store.collection("Codes")
                    documents = collection.where("UserID", "==", deleted_object.UserID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True
                case AverageRating():
                    # remove code and leave.
                    collection = self.fire_store.collection("AverageRating")
                    documents = collection.where("ListingID", "==", deleted_object.ListingID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True
                
                case _:
                    raise TypeError(f"Id_source Not Valid Type: {deleted_object}, {type(deleted_object)}")
        raise IOError("Not Connected to Database")
    
    def get_all_from(self, data_class:T) -> list[T]:
        """Get all data of any one particular type from the database. 

        Uses 1 query

        Args:
            data_class (T): Any of the valid datatypes. dont use a real object just make a new constructor

        Raises:
            IOError: _description_

        Returns:
            list[T]: list of the same type as inputed
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
            case Codes():
                collection = "Codes"
            case AverageRating():
                collection = "AverageRating"

        if self.connected:
            datalist = self._get_data(collection)
            return cast(list[T], [data_class.from_dict(i) for i in datalist])
        else:
            raise IOError("Not Connected")

    def add_object(self,object:DataObject) -> None:
        """Adds an object into the database

        Uses 1 query

        Args:
            object (DataObject): any dataobject

        Raises:
            IOError: not connected to the database
        """
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
            case Codes():
                collection = "Codes"
            case AverageRating():
                collection = "AverageRating"
        if self.connected:
            result = self._push_data(object.as_dict(),collection)
        else:
            raise IOError("Not Connected")
        
    def update_object(self, object:DataObject) -> WriteResult:
        """Updates object in database. Use if the object was modified in any way

        Uses 2 queries. One to get and 1 to update.

        Args:
            object (DataObject): object to update.

        Raises:
            TypeError: Object does not exsist in the database. Invalid id
            IOError: not connected to the database

        Returns:
            WriteResult: write result. not usefull in most cases. ignore
        """
        if self.connected:
            match object:
                case User():
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", object.UserID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one User with UserID: {object.UserID}, there is {len(documents)} of them")
                case Password():
                    collection = self.fire_store.collection("Passwords")
                    documents = collection.where("UserID", "==", object.UserID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Password with UserID: {object.UserID}, there is {len(documents)} of them")
                case Comments():
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("CommentID", "==", object.CommentId).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Comment with CommentId: {object.CommentId}, there is {len(documents)} of them")
                case Landlord():
                    collection = self.fire_store.collection("Landlord")
                    documents = collection.where("LLID", "==", object.LLID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Landlord with LLID: {object.LLID}, there is {len(documents)} of them")
                case Listing():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("ListingID", "==", object.ListingID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Listing with ListingID: {object.ListingID}, there is {len(documents)} of them")
                case Rating():
                    collection = self.fire_store.collection("Rating")
                    documents = collection.where("RatingID", "==", object.RatingID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Rating with RatingID: {object.RatingID}, there is {len(documents)} of them")
                case Codes():
                    collection = self.fire_store.collection("Codes")
                    documents = collection.where("UserID", "==", object.UserID).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Code with UserID: {object.UserID}, there is {len(documents)} of them")
                case AverageRating():
                    collection = self.fire_store.collection("AverageRating")
                    documents = collection.where(filter=FieldFilter("ListingID", "==", object.ListingID)).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one AverageRating with ListingID: {object.ListingID}, there is {len(documents)} of them")
        raise IOError("Not Connected to Database")

    def update_average_rating(self, listing: Listing):
        """Updates the average rating of 1 specific listing

        Uses 3 queries.

        Args:
            listing (Listing): any listing
        """
        # get all ratings for listing
        # average
        ratings = self.get_ratings_from_listing(listing) # 1 query, required

        sum = 0
        count = len(ratings)
        for rating in ratings:
            sum += rating.Rating
        average = sum/count if count != 0 else 0

        ar = AverageRating(listing.ListingID, average, count)
        ref = self.get_average_rating_ref(listing) # 1 query
        
        if ref is not None:  
            collection = self.fire_store.collection("AverageRating")
            print("average rating refrence:",ref.id)
            collection.document(ref.id).update(ar.as_dict()) # 1 query
        else:
            self.add_object(ar)  # 1 query

    def update_all_average_ratings(self):
        """Updates the average rating of all listings

        Uses 3 queries. + up to L updates
        """
        # i can do this in 3
        ratings = self.get_all_from(Rating())
        listings = self.get_all_from(Listing())
        current_averages = self.get_all_from(AverageRating())

        # sort by listing
        ratings_per_listing:dict[str, list[Rating]] = {}
        for r in ratings:
            if r.ListingID in ratings_per_listing:
                ratings_per_listing[r.ListingID].append(r)
                continue
            ratings_per_listing[r.ListingID] = [r]

        known_averages:dict[str, AverageRating] = {}
        for avg in current_averages:
            known_averages[avg.ListingID] = avg
        
        for l in listings: # for n listings
            try:
                ratings = ratings_per_listing[l.ListingID]
            except:
                rating = []

            sum = 0
            count = len(ratings)
            for rating in ratings:
                sum += rating.Rating
            average = sum/count if count != 0 else 0
            if l.ListingID in known_averages:
                if average != known_averages[l.ListingID].AverageRating:
                    self.update_object(AverageRating(l.ListingID, average, count))
            else:
                self.add_object(AverageRating(l.ListingID, average, count))
            
    # Email functions

    def send_code(self, user: User,code:Codes) -> bool:
        """Send an email to any user's email address

        Args:
            user (User): The user we are sending the code to
            code (Codes): The code we are sending

        Returns:
            bool: Whether the email was sent properly or not

        Uses 0 queries.
        """
        subject = "RateMyHousingCode"
        body = f"Your code is {code.Code}"
        with open("src/Secrets2.json") as f:
            secrets = json.decoder.JSONDecoder().decode("".join(f.readlines()))
        sender = secrets["Sender"]
        password = secrets["Password"]

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = user.Email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, user.Email, msg.as_string())
            print(f"Message sent to {user.Email}")
            return True
        return False
    
    def verify_code(self, user: User,code: int) -> bool:
        """Verifies any code send from user is the valid code

        Args:
            user (User): User who's code we are checking
            code (int): the code we want to varify

        Returns:
            bool: true if the code is valid

        Uses 2 queries.
        """
        if self.check_for_code(user):
            c = self.get_code_from_user(user)
            return c.Code == code
        return False

    # check for x functions
    
    def check_for_username(self, username:str) -> bool:
        """Uses username to check for a valid user

        Args:
            username (str): username to check

        Raises:
            IOError: if not connected to database

        Returns:
            bool: valid user or not

        Uses 1 query.
        """
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Username","==",username)
            user = [doc.to_dict() for doc in query.get()]
            return len(user) >= 1
        raise IOError("Not Connected to Database")
   
    def check_for_email(self, email:str) -> bool:
        """Checks to see if an email belongs to a user or not

        Args:
            email (str): email to check

        Raises:
            IOError: if not connected to database

        Returns:
            bool: valid or not

        Uses 1 query.
        """
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Email","==",email)
            user = [doc.to_dict() for doc in query.get()]
            return len(user) >= 1
        raise IOError("Not Connected to Database")

    def get_average_rating_ref(self, listing: Listing) -> DocumentSnapshot | None:
        """gets the average rating refrences from any listing

        Args:
            listing (Listing): Listing to target

        Raises:
            IOError: if not connected to database

        Returns:
            DocumentSnapshot | None: the snapshot of the document that represents the average rating
        """
        if self.connected:
            collection = self.fire_store.collection("AverageRating")
            query = collection.where("ListingID","==",listing.ListingID)
            test = query.get()
            if len(test) >= 1:
                return test[0]
            else:
                return None
        raise IOError("Not Connected to Database")
    
    def check_for_code(self, user: User) -> bool:
        """checks if a user has a code or not

        Args:
            user (User): The user to check for

        Raises:
            IOError: If not connected to database

        Returns:
            bool: true if code exists

        Uses 1 query.
        """
        if self.connected:
            collection = self.fire_store.collection("Codes")
            query = collection.where("UserID","==",user.UserID)
            test = self._unwrap_query(query)
            if len(test) >= 1:
                return True
            else:
                return False
        raise IOError("Not Connected to Database")
    

    # mod tools
    def find_orphend_data(self, data_type:T) -> list[T]:
        """finds all orphens in any particular datatype

        Args:
            data_type (T): The datatype to find orphens for

        Returns:
            list[T]: A list of all ophens

        Uses 1+n queries.
        """
        orphens = []
        match data_type:
            case User():
                # dependent on password
                for user in self.get_all_from(User()):
                    try: self.get_pass_from_user(user)
                    except: orphens.append(user)
            case Rating():
                # dependent on user and listing
                for rating in self.get_all_from(Rating()):
                    try: self.get_user_from_rating(rating)
                    except: 
                        orphens.append(rating)
                        break
                    try: self.get_listing_from_rating(rating)
                    except: orphens.append(rating)
            case Landlord():
                # dependent on nothing
                pass
            case Password():
                # dependent on user
                for password in self.get_all_from(Password()):
                    try: self.get_object_by_id(password.UserID,User())
                    except: orphens.append(password)
            case Comments():
                # dependent on user and Listing
                for com in self.get_all_from(Comments()):
                    try: self.get_listing_from_comments(com)
                    except: 
                        orphens.append(com)
                        break
                    try: self.get_user_from_comments(com)
                    except: 
                        orphens.append(com)
            case Listing():
                # dependent on lanloard
                for listing in self.get_all_from(Listing()):
                    try: self.get_landlord_from_Listing(listing)
                    except: orphens.append(listing)
            case Codes():
                # dependent on user
                for code in self.get_all_from(Codes()):
                    try: self.get_object_by_id(code.UserID,User())
                    except: orphens.append(code)
            case AverageRating():
                # dependent on listing
                for average in self.get_all_from(AverageRating()):
                    try: self.get_object_by_id(average.ListingID,Listing())
                    except: orphens.append(average)
            case _:
                    pass
        return orphens

    def has_missing_data(self, object:dict, data_type:DataObject)-> tuple[bool, list]:
        """checks any onee object to see if it has missing data or not

        Args:
            object (dict): object to check
            data_type (DataObject): the datatype to check this to

        Returns:
            tuple[bool, list]: returns wether the object has missing data or not and where the missing data is

        Uses 0 queries
        """
        missing_keys = []
        result = False
        for field in fields(data_type):
            if field not in object:
                result = True
                missing_keys.append(field)
        return result, missing_keys
    


    # User relations
    # username -> user
    # email -> user
    # user -> password
    # User <-> lanloard
    # user <-> rating (many)
    # user <-> comments (many)
    # User -> Code
    def get_user_with_username(self, username:str) -> User:
        """With a username get a user 

        Args:
            username (str): username to intaragate

        Raises:
            TypeError: no user with that username
            IOError: if not connected with database

        Returns:
            User: user with that username

        Uses 1 query.
        """
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
    
    def get_user_with_email(self, email:str) -> User:
        """Get user with email

        Args:
            email (str): email to look for

        Raises:
            TypeError: no user with that email
            IOError: if not connected with database

        Returns:
            User: user with that email

        Uses 1 query.
        """
        if self.connected:
            collection = self.fire_store.collection("Users")
            query = collection.where("Email","==",email)
            user = self._unwrap_query(query)
            if len(user) == 1:
                user = user[0]
                return User.from_dict(user)
            else:
                raise TypeError(f"no user with the email: {email}")
        raise IOError("Not Connected to Database")

    def get_pass_from_user(self, user:User) -> Password:
        """Get password from a user

        Args:
            user (User): user in question

        Raises:
            TypeError: no password with that userid
            IOError: if not connected to database

        Returns:
            Password: the (hashed) password connected to the user

        Uses 1 query.
        """
        if self.connected:
            password_list = self._get_document_using_id("Passwords",User(),user.UserID)
            if len(password_list) == 1:
                p = password_list[0]
                return Password.from_dict(p)
            else:
                raise TypeError(f"no password with userid: {user.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_landlord_from_user(self, user:User) -> Landlord:
        """get landlord connected to a particular user

        Args:
            user (User): user to get LL of

        Raises:
            TypeError: user has no LLid or no LL with that LLid
            IOError: if not connected to database

        Returns:
            Landlord: landlord connected to that user

        Uses 1 query.
        """
        if self.connected:
            if user.ConnectedLL ==  "":
                raise TypeError(f"User has no LLID")
            Landlord_list = self._get_document_using_id("Landlords", Landlord(),user.ConnectedLL)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord.from_dict(l)
            else:
                raise TypeError(f"no Landlord with LLID: {user.ConnectedLL}")
        raise IOError("Not Connected to Database")

    def get_ratings_from_user(self, user:User) -> list[Rating]:
        """get all ratings origionating from that user

        Args:
            user (User): The user to inspect

        Raises:
            IOError: if not connected to database

        Returns:
            list[Rating]: a list of all ratings made by that user 

        Uses 1 query.
        """
        if self.connected:
            ratings = self._get_document_using_id("Rating", User(),user.UserID)
            return [Rating.from_dict(r) for r in ratings]
        raise IOError("Not Connected to Database")
    
    def get_comments_from_user(self, user:User) -> list[Comments]:
        """get comments made by a specific user

        Args:
            user (User): user to inspect

        Raises:
            IOError: if not connected to database

        Returns:
            list[Comments]: list of all comment sconnected to this user

        Uses 1 query.
        """
        if self.connected:
            coms = self._get_document_using_id("Comments", User(),user.UserID)
            return [Comments.from_dict(c) for c in coms]
        raise IOError("Not Connected to Database")
    
    def get_code_from_user(self, user:User) -> Codes:
        """get a code from a user

        Args:
            user (User): user to get code from

        Raises:
            TypeError: code does not exsist
            IOError: if not connected to that database

        Returns:
            Codes: the activation code for that user

        Uses 1 query.
        """
        if self.connected:
            code_list = self._get_document_using_id("Codes", Codes(),user.UserID)
            if len(code_list) == 1:
                c = code_list[0]
                return Codes.from_dict(c)
            else:
                raise TypeError(f"no code with userid: {user.UserID}")
        raise IOError("Not Connected to Database")
    
    # rating relationships
    # Rating <-> user
    # Rating <-> Listing
    def get_user_from_rating(self,rating:Rating) -> User:
        """get user from rating

        Args:
            rating (Rating): rating to inspect

        Raises:
            TypeError: invalid username
            IOError: if not connected to database

        Returns:
            User: user who posted the rating

        Uses 1 query.
        """
        if self.connected:
            users = self._get_document_using_id("Users",User(),rating.UserID)
            if len(users) == 1:
                u = users[0]
                return User.from_dict(u)
            else:
                raise TypeError(f"no username with userid: {rating.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_listing_from_rating(self,rating:Rating) -> Listing:
        """get listing connected to rating

        Args:
            rating (Rating): rating to inspect

        Raises:
            TypeError: invalid listing
            IOError: if not connect to database

        Returns:
            Listing: listing that rating is on

        Uses 1 query.
        """
        if self.connected:
            listings = self._get_document_using_id("Listing",Listing(),rating.ListingID)
            if len(listings) == 1:
                l = listings[0]
                return Listing.from_dict(l)
            else:
                raise TypeError(f"no listing with ListingID: {rating.ListingID}")
        raise IOError("Not Connected to Database")
    
    # comments relationships
    # comment <-> user
    # comment -> comment
    # comment <-> listing
    def get_user_from_comments(self,comment:Comments) -> User:
        """get user from comments

        Args:
            comment (Comments): the comment to investigate

        Raises:
            TypeError: invalid userid
            IOError: if not connected to database

        Returns:
            User: the user who made the comment

        Uses 1 query.
        """
        if self.connected:
            users = self._get_document_using_id("Users",User(),comment.UserID)
            if len(users) == 1:
                u = users[0]
                return User.from_dict(u)
            else:
                raise TypeError(f"no username with userid: {comment.UserID}")
        raise IOError("Not Connected to Database")
    
    def get_comments_from_comments(self,comment:Comments) -> Comments:
        """get a connected comment from comment a

        Args:
            comment (Comments): the comment to start at

        Raises:
            TypeError: no valid connected comment 
            IOError: if not connected to database

        Returns:
            Comments: a comment that "replys" to the current comment

        Uses 1 query.
        """
        if self.connected:
            com = self._get_document_using_id("Comments",Comments(),comment.ConnectedCommentID)
            if len(com) == 1:
                c = com[0]
                return Comments.from_dict(c)
            else:
                raise TypeError(f"no comment with comment: {comment.ConnectedCommentID}")
        raise IOError("Not Connected to Database")
    
    def get_listing_from_comments(self,comment:Comments) -> Listing:
        """get the listing the comment is on

        Args:
            comment (Comments): comment to invistigate

        Raises:
            TypeError: listing is not real
            IOError: if not connected to database

        Returns:
            Listing: listing comment is connected to

        Uses 1 query.
        """
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
    # listing -> Average rating
    def get_landlord_from_Listing(self, listing:Listing) -> Landlord:
        """get the landlord who made a specific listing

        Args:
            listing (Listing): the listing in question

        Raises:
            TypeError: invalid landlord
            IOError: if not connected to database

        Returns:
            Landlord: landlord connected to this listing

        Uses 1 query.
        """
        if self.connected:
            Landlord_list = self._get_document_using_id("Landlords", Landlord(),listing.LLID)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Landlord.from_dict(l)
            else:
                raise TypeError(f"no Landlord with LLID: {listing.LLID}")
        raise IOError("Not Connected to Database")
    
    def get_ratings_from_listing(self, listing:Listing) -> list[Rating]:
        """get all ratings from a specific listing

        Args:
            listing (Listing): listing to investigate

        Raises:
            IOError: if not connected to database

        Returns:
            list[Rating]: a list of all ratings connected to that listing

        Uses 1 query.
        """
        if self.connected:
            ratings = self._get_document_using_id("Rating", Listing(),listing.ListingID)
            return [Rating.from_dict(r) for r in ratings]
        raise IOError("Not Connected to Database")
    
    def get_comments_from_listing(self, listing:Listing) -> list[Comments]:
        """get all comments that belong to a listing

        Args:
            listing (Listing): the listing in question

        Raises:
            IOError: if not connected to database

        Returns:
            list[Comments]: a list of all comments talking about the server

        Uses 1 query.
        """
        if self.connected:
            coms = self._get_document_using_id("Comments", Listing(),listing.ListingID)
            return [Comments.from_dict(c) for c in coms]
        raise IOError("Not Connected to Database")
    
    def get_average_rating_from_listing(self, listing:Listing) -> AverageRating:
        """gets the average rating from a listing

        Args:
            listing (Listing): listing to calculate

        Raises:
            TypeError: non exsistent average rating
            IOError: if nor connected to database

        Returns:
            AverageRating: average rating of that listing

        Uses 1 query.
        """
        if self.connected:
            ars = self._get_document_using_id("AverageRating", AverageRating(),listing.ListingID)
            if len(ars) == 1:
                ar = ars[0]
                return AverageRating.from_dict(ar)
            else:
                raise TypeError(f"no AverageRating with ListingID: {listing.LLID}")
        raise IOError("Not Connected to Database")
    
    # landlord rlationships
    # Landlord <-> User (many)
    # Landlord <-> Listing (many)
    def get_connected_users_with_landlord(self, landlord:Landlord) -> list[User]:
        """gets all users connected to that landlord

        Args:
            landlord (Landlord): landlord in question

        Raises:
            IOError: if not connected to database

        Returns:
            list[User]: a full list of all users connected to a landlord

        Uses 1 query.
        """
        if self.connected:
            users = self._get_document_using_id("Users", Landlord(),landlord.LLID)
            return [User.from_dict(u) for u in users]
        raise IOError("Not Connected to Database")
    
    def get_connected_listings_with_landlord(self, landlord:Landlord) -> list[Listing]:
        """get all listings the belong to a specific landlord

        Args:
            landlord (Landlord): landlord in question

        Raises:
            IOError: if not connected to database

        Returns:
            list[Listing]: all listings conneceted to landlord

        Uses 1 query.
        """
        if self.connected:
            listings = self._get_document_using_id("Listing", Landlord(),landlord.LLID)
            return [Listing.from_dict(l) for l in listings]
        raise IOError("Not Connected to Database")