# todo: implement unit tests

from src import main
import pytest
from flask import Response


@pytest.fixture
def client():
    """
    A fixture to create a test client for the Flask application.

    Returns:
        FlaskClient: A test client for the Flask application.
    """
    app = main.app
    app.testing = True
    with app.test_client() as client:
        yield client


def test_youtube_endpoint(client):
    """
    Test the `/youtube` endpoint.

    Args:
        client (FlaskClient): The Flask test client.

    Returns:
        None
    """
    # Define a sample payload for the `/youtube` endpoint
    payload = {
        "link": "https://www.youtube.com/watch?v=XJNO492juTE",
        "language_code": "de_DE",
        "source_language": "de",
        "target_language": "en"
    }

    # Send a POST request to the `/youtube` endpoint
    response: Response = client.post('/youtube', json=payload)

    # Assert the response status code is 200
    assert response.status_code == 200

    # Assert the response data is 'Success'
    assert response.data.decode() == 'Success'


def test_video_file_endpoint(client):
    """
    Test the `/video_file` endpoint.

    Args:
        client (FlaskClient): The Flask test client.

    Returns:
        None
    """
    # Define a sample payload for the `/video_file` endpoint
    payload = {
        "language_code": "de_DE",
        "source_language": "de",
        "target_language": "en"
    }

    # Send a POST request to the `/video_file` endpoint
    response: Response = client.post('/video_file', json=payload)

    # Assert the response status code is 200
    assert response.status_code == 200

    # Assert the response data is 'Success'
    assert response.data.decode() == 'Success'
