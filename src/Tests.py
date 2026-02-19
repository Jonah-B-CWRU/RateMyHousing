import secrets
import unittest

import src.Database as database
import src.LoginProcessor as login

db = database.database_manager()

class TestDatabaseMethods(unittest.TestCase):

    def test_connection(self):
        db.connect_to_database()
        self.assertTrue(db.connected)

    def test_addition_and_removal_for_all(self):
        db.connect_to_database()
        # user
        u = database.User(UserID="Test")
        db.add_user(u)
        self.assertTrue(db.recursive_deletion(u))

        # password
        p = database.Password(UserID="Test")
        db.add_passwords(p)
        self.assertTrue(db.recursive_deletion(p))

        # rating
        r = database.Rating(RatingID="Test")
        db.add_rating(r)
        self.assertTrue(db.recursive_deletion(r))
        
        # landlord
        la = database.Landlord(LLID="Test1")
        db.add_landlord(la)
        self.assertTrue(db.recursive_deletion(la))

        # listing
        li = database.Listing(ListingID="Test")
        db.add_listing(li)
        self.assertTrue(db.recursive_deletion(li))

        # comments
        c = database.Comments(CommentId="Test")
        db.add_comment(c)
        self.assertTrue(db.recursive_deletion(c))

    def test_relating_userpass(self):
        db.connect_to_database()

        # add test user/pass to db
        r = str(secrets.token_hex(16))
        u = database.User(UserID=r)
        password = login.PasswordAttempt(r,r)
        p = database.Password(password.hash,password.salt,r)
        
        db.add_user(u)
        db.add_passwords(p)

        # capture test
        test_pass = db.get_pass_from_user(user=u)

        # remove user and pass
        db.recursive_deletion(u)

        # assert test
        self.assertDictEqual(p.as_dict(),test_pass.as_dict())

    

        
if __name__ == '__main__':
    unittest.main()