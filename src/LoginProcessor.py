import secrets,hashlib
from io import BytesIO
from src.Caching import cache_manager
from src.Database import User
from datetime import datetime, timezone


class PasswordAttempt:
	
	userid = ""
	_password = ""
	salt:str = ""
	hash = ""
	
	def __init__(self, userid: str, password: str, salt: str|None=None):
		self.userid = userid
		self._password = password # Change from Jonah's version to make it work
		if salt == None:
			self.genSalt()
		else:
			self.salt = salt
		self.genHash()
	
	def genSalt(self) -> str:
		self.salt = secrets.token_hex(32)
		return self.salt
	
	def genHash(self) -> bytes:
		if self.salt != None:
			self.hash = hashlib.pbkdf2_hmac('sha256', self._password.encode(), self.salt.encode(), 600000).hex()
			return self.hash.encode()
		else:
			self.hash = hashlib.pbkdf2_hmac('sha256', self._password.encode(), "".encode(), 600000).hex()
			return self.hash.encode()

def get_known_users() -> dict[str, User]:
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
	if f"known_users" in cache_man.all_refrences:
		cache_man.update_cache(users, cache_man.all_refrences["known_users"], timeout_seconds=86400)
	else:
		cache_man.add_to_cache(users, "known_users", timeout_seconds=86400)