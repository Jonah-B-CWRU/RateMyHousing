from dataclasses import dataclass, asdict
from typing import Any, TypeAlias, TypeVar, cast
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.query import Query
from google.protobuf import timestamp_pb2
from email.mime.text import MIMEText
import firebase_admin
import json  
import smtplib

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
    def from_dict(dict: dict[str,Any]) -> "Comments":
        try:
            return Comments(
                dict["CommentId"],
                dict["ConnectedCommentID"],
                dict["ListingID"],
                dict["UserID"],
                dict["Content"],
            )
        except:
            return Comments()

@dataclass
class Landlord:
    LLID: str = ""
    Name: str = ""
    Email: str = ""
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> "Landlord":
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
    def from_dict(dict: dict[str,Any]) -> "Listing":
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
    def from_dict(dict: dict[str,Any]) -> "Rating":
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
    def from_dict(dict: dict[str,Any]) -> "Password":
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
    def from_dict(dict: dict[str,Any]) -> "User":
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
    Code: int = 0
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> "Codes":
        return Codes(
            dict["UserID"],
            dict["Code"],
        )

@dataclass
class AverageRating:
    ListingID: str = ""
    AverageRating: float = 0.0
    NumberOfRatings: int = 0
    def as_dict(self) -> dict:
        return asdict(self)
    @staticmethod
    def from_dict(dict: dict[str,Any]) -> "AverageRating":
        return AverageRating(
            dict["ListingID"],
            dict["AverageRating"],
            dict["NumberOfRating"],
        )


# super type alias
DataObject: TypeAlias = User | Rating | Landlord | Password | Comments | Listing | Codes | AverageRating

T = TypeVar("T", bound=DataObject)
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
    
    # basic data handeling
    def _get_data(self, col:str) -> list[dict[str,Any]]:
        """
        Docstring for _get_data
        
        :param self: Data Manager
        :param col: Collection Name
        :type col: str
        :return: list of all raw data taken directly from database 
        :rtype: list[dict[str, Any]]
        """
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
    
    def _unwrap_query(self, q:Query) -> list[dict]:
        total_data:list[dict] = []
        for doc in q.get():
            data = doc.to_dict()
            if data != None:
                total_data.append(data)
        return total_data
    
    def _get_document_using_id(self,collection_to_search:str, Id_type:DataObject, Id_to_look_for:str)-> list[dict]:
        """
        Searches the specified collection for all documents with the corresponding ID.
        
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

    # basic object handeling
    def get_object_by_id(self, id:str, object_type:T) -> T:
        """
        Docstring for get_object_by_id
        
        :param self: data manager
        :param id: ID filtering for
        :type id: id
        :param object_type: the type of object we are looking for
        :type object_type: DataObject
        :return: the object with the id
        :rtype: DataObject
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
                    collection = self.fire_store.collection("Listing")
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
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("UserID", "==", deleted_object.UserID).get()
                    if len(documents) == 1:
                        self.fire_store.recursive_delete(documents[0].reference)
                    else:
                        return False
                    return True
                case AverageRating():
                    # remove code and leave.
                    collection = self.fire_store.collection("Comments")
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
        """
        Get all records from any particar dataclass
        
        :param self: data manager
        :param data_class: the data type you want to get
        :type data_class: DataObject
        :return: all of the table from the data type you asked for
        :rtype: list[DataObject]
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

    def add_object(self,object:DataObject):
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
        
    def update_object(self, object:DataObject):
        if self.connected:
            match object:
                case User():
                    collection = self.fire_store.collection("Users")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one User with UserID: {id}, there is {len(documents)} of them")
                case Password():
                    collection = self.fire_store.collection("Passwords")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Password with UserID: {id}, there is {len(documents)} of them")
                case Comments():
                    collection = self.fire_store.collection("Comments")
                    documents = collection.where("CommentID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Comment with CommentId: {id}, there is {len(documents)} of them")
                case Landlord():
                    collection = self.fire_store.collection("Landlord")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Landlord with LLID: {id}, there is {len(documents)} of them")
                case Listing():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("LLID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Listing with ListingID: {id}, there is {len(documents)} of them")
                case Rating():
                    collection = self.fire_store.collection("Listing")
                    documents = collection.where("RatingID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Rating with RatingID: {id}, there is {len(documents)} of them")
                case Codes():
                    collection = self.fire_store.collection("Codes")
                    documents = collection.where("UserID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one Code with UserID: {id}, there is {len(documents)} of them")
                case AverageRating():
                    collection = self.fire_store.collection("AverageRating")
                    documents = collection.where("ListingID", "==", id).get()
                    if len(documents) == 1:
                        refrence = documents[0]
                        return collection.document(refrence.id).update(object.as_dict())
                    raise TypeError(f"No one AverageRating with ListingID: {id}, there is {len(documents)} of them")
        raise IOError("Not Connected to Database")

    def update_average_rating(self, listing: Listing):
        # get all ratings for listing
        # average
        ratings = self.get_ratings_from_listing(listing)

        sum = 0
        count = len(ratings)
        for rating in ratings:
            sum += rating.Rating
        average = sum/count

        ar = AverageRating(listing.ListingID, average, count)
        if self.check_for_average_rating(listing):
            self.update_object(ar)
        else:
            self.add_object(ar)

    def update_all_average_ratings(self):
        for l in self.get_all_from(Listing()): 
            self.update_average_rating(l)

    # Email functions

    def send_code(self, user: User,code:Codes) -> bool:
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
    
    def verify_code(self, user: User,code: int):
        if self.check_for_code(user):
            c = self.get_code_from_user(user)
            return c == code
        return False

    # check for x functions
    
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

    def check_for_average_rating(self, listing: Listing):
        if self.connected:
            collection = self.fire_store.collection("AverageRating")
            query = collection.where("ListingID","==",listing.ListingID)
            test = self._unwrap_query(query)
            if len(test) >= 1:
                return True
            else:
                return False
        raise IOError("Not Connected to Database")
    
    def check_for_code(self, user: User):
        if self.connected:
            collection = self.fire_store.collection("Codes")
            query = collection.where("UserID","==",user.UserID)
            test = self._unwrap_query(query)
            if len(test) >= 1:
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
    # User -> Code
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
    
    def get_code_from_user(self, user:User) -> Codes:
        if self.connected:
            if user.ConnectedLL ==  "":
                raise TypeError(f"User has no LLID")
            Landlord_list = self._get_document_using_id("Codes", Codes(),user.UserID)
            if len(Landlord_list) == 1:
                l = Landlord_list[0]
                return Codes.from_dict(l)
            else:
                raise TypeError(f"no Lanloard with LLID: {user.ConnectedLL}")
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
    

    # 