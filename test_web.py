from fastapi.testclient import TestClient # type: ignore
from unittest.mock import MagicMock, patch
import pytest # type: ignore
from unittest.mock import patch
import web

# NEEDS PYTHON 3.10 in venv

@pytest.fixture(autouse=True)
def disable_db():
    with patch.object(web.data_man, "connect_to_database"):
        yield



client = TestClient(web.app)

def test_index_page():
    with patch.object(web.data_man, "get_all_from", return_value=[]):
        response = client.get("/")
        assert response.status_code == 200
        assert "Home" in response.text


def test_login_page_get():
    response = client.get("/login")
    assert response.status_code == 200


def test_dashboard_requires_login():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "You must log in" in response.text

def test_login_success():
    with patch("web.verify_login", return_value=True):
        response = client.post(
        "/login",
        data={
            "username": "test@case.edu",
            "password": "password"
        },
        follow_redirects=False
)
        assert response.status_code == 302
        assert response.cookies.get("username").strip('"') == "test@case.edu"


def test_login_failure():
    with patch("web.verify_login", return_value=False):
        response = client.post("/login", data={
            "username": "bad@case.edu",
            "password": "wrong"
        })
        assert response.status_code == 200
        assert "Invalid username or password" in response.text


def test_create_user_success():
    with patch("web.add_user", return_value=(True, "User created successfully")):
        response = client.post("/create", data={
            "username": "test@case.edu",
            "password": "password"
        })
        assert response.status_code == 200
        assert "User created successfully" in response.text


def test_create_user_failure():
    with patch("web.add_user", return_value=(False, "Username already exists")):
        response = client.post("/create", data={
            "username": "test@case.edu",
            "password": "password"
        })
        assert response.status_code == 200
        assert "Username already exists" in response.text

def test_add_comment_requires_login():
    with patch.object(web.data_man, "connected", True), \
         patch.object(web.data_man, "get_user_with_username", return_value=None):
        
        response = client.post(
            "/add_comment",
            data={
                "listing_id": "abc",
                "comment": "Nice place"
            }
        )
        
        assert response.status_code == 200
        assert "You must log in" in response.text


def test_add_comment_success():
    mock_user = MagicMock()
    mock_user.UserID = "user123"

    with patch.object(web.data_man, "connect_to_database"), \
         patch.object(web.data_man, "get_user_with_username", return_value=mock_user), \
         patch.object(web.data_man, "add_object"):

        response = client.post(
            "/add_comment",
            data={
                "listing_id": "abc",
                "comment": "Nice place",
                "tags_location": ["Quiet"],
                "tags_condition": [],
                "tags_landlord": [],
                "tags_value": []
            },
            cookies={"username": "test@case.edu"},
            follow_redirects=False
        )

        assert response.status_code == 302


def test_validate_tags_valid():
    valid, msg = web.validate_tags(["Quiet", "Clean"])
    assert valid is True


def test_validate_tags_invalid_group_duplicate():
    valid, msg = web.validate_tags(["Quiet", "Noisy"])
    assert valid is False


def test_validate_tags_invalid_tag():
    valid, msg = web.validate_tags(["FakeTag"])
    assert valid is False


def test_view_listings():
    mock_listing = MagicMock()
    mock_listing.CreatedAt = ""

    mock_ar = MagicMock()
    mock_ar.NumberOfRatings = 1
    mock_ar.AverageRating = 5.0

    with patch.object(web.data_man, "get_all_from", return_value=[mock_listing]), \
         patch.object(web.data_man, "get_comments_from_listing", return_value=[]), \
         patch.object(web.data_man, "check_for_average_rating", return_value=True), \
         patch.object(web.data_man, "update_average_rating"), \
         patch.object(web.data_man, "get_average_rating_from_listing", return_value=mock_ar):

        response = client.get("/listings")
        assert response.status_code == 200