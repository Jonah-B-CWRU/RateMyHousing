import secrets,hashlib
from io import BytesIO
from src.Caching import cache_manager
from src.Database import User
from datetime import datetime, timezone


class PasswordAttempt:
    """A class encapsulating the information needed to attempt a login. Includes methods
    for generating a new password hash or generating a hash using an extant salt

    Returns:
        PasswordAttempt: An object encapsulating a userid, password, salt, and generated hash
    """
    
    userid = ""
    _password = ""
    salt:str = ""
    hash = ""
    
    def __init__(self, userid: str, password: str, salt: str|None=None):
        """Initializes a new PasswordAttempt

        Args:
            userid (str): The User ID that the login attempt is connected to
            password (str): The plaintext password that a hash will be generated for
            salt (str | None, optional): The salt that will be used in hashing the password.
                Defaults to a randomly generated salt.
        """
        self.userid = userid
        self._password = password # Change from Jonah's version to make it work
        if salt == None:
            self.genSalt()
        else:
            self.salt = salt
        self.genHash()
    
    def genSalt(self) -> str:
        """Generates a salt for a login attempt if none is provided

        Returns:
            str: 32 bytes of hexadecimal that will be used as the salt
        """
        self.salt = secrets.token_hex(32)
        return self.salt
    
    def genHash(self) -> bytes:
        """Generates a hash for the plaintext password provided using the salt.
        We use PBKDF2 to comply with current hash security reccomendations

        Returns:
            bytes: A series of bytes representing the hashed password
        """
        if self.salt != None:
            self.hash = hashlib.pbkdf2_hmac('sha256', self._password.encode(), self.salt.encode(), 600000).hex()
            return self.hash.encode()
        else:
            self.hash = hashlib.pbkdf2_hmac('sha256', self._password.encode(), "".encode(), 600000).hex()
            return self.hash.encode()

def get_known_users() -> dict[str, User]:
    """Fetches all users currently known to the cache

    Returns:
        dict[str, User]: A dictionary containing each user as a `User` object with each key being the user ID
    """
    cache_man = cache_manager()
    if f"known_users" in cache_man.all_refrences:
        print("known users found")
        cache_data = cache_man.get_cache("known_users")
        if cache_data.cache_max_age > datetime.now():
            data:dict[str,dict] = cache_data.cache_data
            out:dict[str, User] = {}
            # now transform this data into usernames
            for key in data.keys():
                out[key] = User.from_dict(data[key])
            return out
        else: 
            return {}
    return {}

def update_known_users(users: dict[str, User], cache_man: cache_manager):
    """Updates the cache with a new list of currently known users

    Args:
        users (dict[str, User]): The updated list of users
        cache_man (cache_manager): The cache_manager instance being used to update the cache
    """
    if f"known_users" in cache_man.all_refrences:
        cache_man.update_cache(users, cache_man.all_refrences["known_users"], timeout_seconds=86400)
    else:
        cache_man.add_to_cache(users, "known_users", timeout_seconds=86400)