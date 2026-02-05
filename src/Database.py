from typing import Any
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from dataclasses import dataclass, asdict
from google.protobuf import timestamp_pb2
import firebase_admin

# all dataclasses's for easy use
@dataclass
class Comments:
    CommentId: str
    ConnectedCommentID: str
    ListingID: str
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Landlords:
    LLID: str
    Name: str
    Email: str
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Listing:
    ListingID: str
    LLID: str
    ListingLocation: str
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Rating:
    ratingID: str
    UserID: str
    Rating: int
    def as_dict(self) -> dict:
        return asdict(self)

@dataclass
class Password:
    Hash: str
    Salt: str
    UserID: str
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
        else: 
            print("Already connected")
    
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
	
    # def add_comment(self, comment:Comments):
        # if self.connected:
            # result = self._push_data(comment.as_dict(),"Comments")
