import secrets,hashlib
from io import BytesIO



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

		