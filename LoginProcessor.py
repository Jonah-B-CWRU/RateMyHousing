import secrets,hashlib
from io import BytesIO

class PasswordAttempt:
	
	userid = 0
	_password = ""
	salt = ""
	hash = ""
	
	def __init__(self, userid: int, password: str, salt: str=None):
		self.userid = userid
		self.password = password
		self.salt = salt
	
	def genSalt(self) -> str:
		self.salt = secrets.token_hex(32)
		return self.salt
	
	def genHash(self) -> bytes:
		self.hash = hashlib.pbkdf2_hmac('sha256', self._password.encode(), self.salt.encode(), 600000).hex()
		return self.hash
		