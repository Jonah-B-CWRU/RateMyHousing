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
        db.add_object(u)
        self.assertTrue(db.recursive_deletion(u))

        # password
        p = database.Password(UserID="Test")
        db.add_object(p)
        self.assertTrue(db.recursive_deletion(p))

        # rating
        r = database.Rating(RatingID="Test")
        db.add_object(r)
        self.assertTrue(db.recursive_deletion(r))
        
        # landlord
        la = database.Landlord(LLID="Test1")
        db.add_object(la)
        self.assertTrue(db.recursive_deletion(la))

        # listing
        li = database.Listing(ListingID="Test")
        db.add_object(li)
        self.assertTrue(db.recursive_deletion(li))

        # comments
        c = database.Comments(CommentId="Test")
        db.add_object(c)
        self.assertTrue(db.recursive_deletion(c))

        # codes
        c = database.Codes(UserID="Test")
        db.add_object(c)
        self.assertTrue(db.recursive_deletion(c))

        # AverageRating
        a = database.AverageRating(ListingID="Test")
        db.add_object(a)
        self.assertTrue(db.recursive_deletion(a))

    def test_user_relations(self):
        """
        Tests all of the following relations

        User relations
        username -> user
        email -> user
        user -> password
        User <-> lanloard
        user <-> rating (many)
        user <-> comments (many)
        User -> Code
        """
        db.connect_to_database()

        # add test data to db

        # landlord
        r_llid = str(secrets.token_hex(16))
        lan = database.Landlord(LLID=r_llid)

        # user
        r_userid = str(secrets.token_hex(16))
        r_email = str(secrets.token_hex(16))
        r_username = str(secrets.token_hex(16))
        usr = database.User(UserID=r_userid, Email=r_email,Username=r_username, ConnectedLL=r_llid)

        # password
        r_password = str(secrets.token_hex(16))
        password = login.PasswordAttempt(r_userid,r_password)
        pas = database.Password(password.hash,password.salt,r_userid)

        # rating
        r_ratid = str(secrets.token_hex(16))
        rat = database.Rating(RatingID=r_ratid,UserID=r_userid)

        # comment
        r_comid = str(secrets.token_hex(16))
        com = database.Comments(CommentId=r_comid,UserID=r_userid)

        # code
        cod = database.Codes(r_userid)

        # add all data
        db.add_object(lan)
        db.add_object(usr)
        db.add_object(pas)
        db.add_object(rat)
        db.add_object(com)
        db.add_object(cod)

        # capture test data
        t_username = db.get_user_with_username(r_username)
        t_email = db.get_user_with_email(r_email)
        t_pas = db.get_pass_from_user(usr)
        t_ll = db.get_landlord_from_user(usr)
        t_rats = db.get_ratings_from_user(usr)
        t_coms = db.get_comments_from_user(usr)
        t_cod = db.get_code_from_user(usr)
        

        # remove all data (do here so if tests fail data isnt stuck)
        db.recursive_deletion(usr)
        db.recursive_deletion(lan)

        # assert tests
        self.assertDictEqual(usr.as_dict(),t_username.as_dict())
        self.assertDictEqual(usr.as_dict(),t_email.as_dict())
        self.assertDictEqual(pas.as_dict(),t_pas.as_dict())
        self.assertDictEqual(lan.as_dict(),t_ll.as_dict())
        self.assertDictEqual(rat.as_dict(),t_rats[0].as_dict())
        self.assertDictEqual(com.as_dict(),t_coms[0].as_dict())
        self.assertDictEqual(cod.as_dict(),t_cod.as_dict())
    
    def test_rating_relations(self):
        """
        Tests all of the following relations

        Rating relationships
        Rating <-> user
        Rating <-> Listing
        """
        db.connect_to_database()

        # --- add test data to db ---

        # landlord (required for listing)
        r_llid = str(secrets.token_hex(16))
        lan = database.Landlord(LLID=r_llid)

        # user
        r_userid = str(secrets.token_hex(16))
        usr = database.User(UserID=r_userid)

        # listing
        r_listid = str(secrets.token_hex(16))
        lst = database.Listing(ListingID=r_listid, LLID=r_llid)

        # rating (the bridge between user and listing)
        r_ratid = str(secrets.token_hex(16))
        rat = database.Rating(RatingID=r_ratid, UserID=r_userid, ListingID=r_listid, Rating=5)

        # add all data
        db.add_object(lan)
        db.add_object(usr)
        db.add_object(lst)
        db.add_object(rat)

        # --- capture test data ---

        # Testing Rating <-> User
        t_user_from_rat = db.get_user_from_rating(rat)
        t_rats_from_user = db.get_ratings_from_user(usr)

        # Testing Rating <-> Listing
        t_listing_from_rat = db.get_listing_from_rating(rat)
        t_rats_from_listing = db.get_ratings_from_listing(lst)

        # --- remove all data ---
        # recursive_deletion handles dependencies
        db.recursive_deletion(lan)
        db.recursive_deletion(usr)

        # --- assert tests ---

        # Assert User relation
        self.assertDictEqual(usr.as_dict(), t_user_from_rat.as_dict())
        self.assertDictEqual(rat.as_dict(), t_rats_from_user[0].as_dict())

        # Assert Listing relation
        self.assertDictEqual(lst.as_dict(), t_listing_from_rat.as_dict())
        self.assertDictEqual(rat.as_dict(), t_rats_from_listing[0].as_dict())

    def test_comment_relations(self):
        """
        Tests all of the following relations

        Comments relationships
        comment <-> user
        comment -> comment (Parent/Child)
        comment <-> listing
        """
        db.connect_to_database()

        # --- add test data to db ---

        # landlord (required for listing)
        r_llid = str(secrets.token_hex(16))
        lan = database.Landlord(LLID=r_llid)

        # user
        r_userid = str(secrets.token_hex(16))
        usr = database.User(UserID=r_userid)

        # listing
        r_listid = str(secrets.token_hex(16))
        lst = database.Listing(ListingID=r_listid, LLID=r_llid)

        # parent comment
        r_comid_parent = str(secrets.token_hex(16))
        com_parent = database.Comments(
            CommentId=r_comid_parent, 
            UserID=r_userid, 
            ListingID=r_listid, 
            Content="This is a parent comment"
        )

        # child comment (comment -> comment)
        r_comid_child = str(secrets.token_hex(16))
        com_child = database.Comments(
            CommentId=r_comid_child, 
            ConnectedCommentID=r_comid_parent, 
            UserID=r_userid, 
            ListingID=r_listid, 
            Content="This is a reply"
        )

        # add all data
        db.add_object(lan)
        db.add_object(usr)
        db.add_object(lst)
        db.add_object(com_parent)
        db.add_object(com_child)

        # --- capture test data ---

        # comment <-> user
        t_user_from_com = db.get_user_from_comments(com_parent)
        t_coms_from_user = db.get_comments_from_user(usr)

        # comment <-> listing
        t_listing_from_com = db.get_listing_from_comments(com_parent)
        t_coms_from_listing = db.get_comments_from_listing(lst)

        # comment -> comment (child fetches parent)
        t_parent_com = db.get_comments_from_comments(com_child)

        # --- remove all data ---
        # recursive_deletion on the root entities
        db.recursive_deletion(usr)
        db.recursive_deletion(lan)

        # --- assert tests ---

        # Assert User relation
        self.assertDictEqual(usr.as_dict(), t_user_from_com.as_dict())
        self.assertTrue(any(c.CommentId == r_comid_parent for c in t_coms_from_user))

        # Assert Listing relation
        self.assertDictEqual(lst.as_dict(), t_listing_from_com.as_dict())
        self.assertTrue(any(c.CommentId == r_comid_parent for c in t_coms_from_listing))

        # Assert Comment -> Comment relation
        self.assertDictEqual(com_parent.as_dict(), t_parent_com.as_dict())

    def test_listing_relations(self):
        """
        Tests all of the following relations

        Listing relationships
        listing -> landlord
        listing <-> Rating (many)
        listing <-> Comments (many)
        listing -> Average rating
        """
        db.connect_to_database()

        # --- add test data to db ---

        # landlord (root for listing)
        r_llid = str(secrets.token_hex(16))
        lan = database.Landlord(LLID=r_llid)

        # user (required for ratings/comments)
        r_userid = str(secrets.token_hex(16))
        usr = database.User(UserID=r_userid)

        # listing
        r_listid = str(secrets.token_hex(16))
        lst = database.Listing(ListingID=r_listid, LLID=r_llid)

        # rating
        r_ratid = str(secrets.token_hex(16))
        rat = database.Rating(RatingID=r_ratid, UserID=r_userid, ListingID=r_listid, Rating=4)

        # average rating (usually a calculated/view object in many systems, 
        # but treated as an object to add here based on your dataclass)
        avg_rat = database.AverageRating(ListingID=r_listid, AverageRating=4.0, NumberOfRatings=1)

        # comment
        r_comid = str(secrets.token_hex(16))
        com = database.Comments(CommentId=r_comid, UserID=r_userid, ListingID=r_listid)

        # add all data
        db.add_object(lan)
        db.add_object(usr)
        db.add_object(lst)
        db.add_object(rat)
        db.add_object(avg_rat)
        db.add_object(com)

        # --- capture test data ---

        # listing -> landlord
        t_ll = db.get_landlord_from_Listing(lst)

        # listing <-> Rating (many)
        t_rats = db.get_ratings_from_listing(lst)

        # listing <-> Comments (many)
        t_coms = db.get_comments_from_listing(lst)

        # listing -> Average rating
        t_avg = db.get_average_rating_from_listing(lst)

        # --- remove all data ---
        # recursive_deletion on roots
        db.recursive_deletion(lan)
        db.recursive_deletion(usr)

        # --- assert tests ---

        # Assert Landlord relation
        self.assertDictEqual(lan.as_dict(), t_ll.as_dict())

        # Assert Ratings (many)
        self.assertDictEqual(rat.as_dict(), t_rats[0].as_dict())

        # Assert Comments (many)
        self.assertDictEqual(com.as_dict(), t_coms[0].as_dict())

        # Assert Average Rating
        self.assertDictEqual(avg_rat.as_dict(), t_avg.as_dict())
    
    def test_landlord_relations(self):
        """
        Tests all of the following relations

        Landlord relationships
        Landlord <-> User (many)
        Landlord <-> Listing (many)
        """
        db.connect_to_database()

        # --- add test data to db ---

        # landlord (the root)
        r_llid = str(secrets.token_hex(16))
        lan = database.Landlord(LLID=r_llid, Name="Test Landlord")

        # users (many)
        r_userid_1 = str(secrets.token_hex(16))
        r_userid_2 = str(secrets.token_hex(16))
        usr1 = database.User(UserID=r_userid_1, Username="Tenant1", ConnectedLL=r_llid)
        usr2 = database.User(UserID=r_userid_2, Username="Tenant2", ConnectedLL=r_llid)

        # listings (many)
        r_listid_1 = str(secrets.token_hex(16))
        r_listid_2 = str(secrets.token_hex(16))
        lst1 = database.Listing(ListingID=r_listid_1, LLID=r_llid, Address="123 Alpha St")
        lst2 = database.Listing(ListingID=r_listid_2, LLID=r_llid, Address="456 Beta Ave")

        # add all data
        db.add_object(lan)
        db.add_object(usr1)
        db.add_object(usr2)
        db.add_object(lst1)
        db.add_object(lst2)

        # --- capture test data ---

        # Landlord <-> User (many)
        t_users = db.get_connected_users_with_landlord(lan)

        # Landlord <-> Listing (many)
        t_listings = db.get_connected_listings_with_landlord(lan)

        # --- remove all data ---
        # Since everything hinges on the Landlord ID, one call should clear it all
        db.recursive_deletion(lan)

        # --- assert tests ---

        # Assert Users (many)
        # Checking for length and that the correct IDs are present
        self.assertEqual(len(t_users), 2)
        user_ids = [u.UserID for u in t_users]
        self.assertIn(r_userid_1, user_ids)
        self.assertIn(r_userid_2, user_ids)

        # Assert Listings (many)
        self.assertEqual(len(t_listings), 2)
        listing_ids = [l.ListingID for l in t_listings]
        self.assertIn(r_listid_1, listing_ids)
        self.assertIn(r_listid_2, listing_ids)
if __name__ == '__main__':
    unittest.main()