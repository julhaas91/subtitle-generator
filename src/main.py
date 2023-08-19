import os

from flask import Flask, Response, request
from flask_cors import CORS

from src import process
from src import helpers
from src.common import logger

from dotenv import load_dotenv

app = Flask(__name__)

# Set CORS headers for the preflight request
CORS(app)

# Set response header
response_headers = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
}

# load env vars
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
location = "global"


@app.route("/youtube", methods=["POST"])
def youtube() -> Response:
    """
    This function handles the POST request for the "/youtube" endpoint.

    Example payload:
        payload = {
        "link": "https://www.youtube.com/watch?v=XJNO492juTE",
        "language_code": "de_DE",
        "source_language": "de",
        "target_language": "en"
        }

    Returns:
        Response: The response object containing the result of the request.
    """

    payload = request.get_json()

    # Check if all required fields are present - if not return error
    required_fields = ["link", "language_code", "source_language", "target_language"]
    msg = helpers.check_payload_fields(required_fields, payload)
    if msg:
        return Response(msg, 400, response_headers)

    # video
    youtube_link = payload["link"]
    video_filename = "video.mp4"
    video_blob_name = f"videos/{video_filename}"
    gcs_uri_video = f"gs://{BUCKET_NAME}/{video_blob_name}"

    # audio
    audio_filename = "audio.wav"
    audio_blob_name = f"audios/{audio_filename}"
    gcs_uri_audio = f"gs://{BUCKET_NAME}/{audio_blob_name}"

    # translation_api
    source_language = payload["source_language"]  # de
    target_language = payload["target_language"]  # en
    gcs_uri_text_translation_result = f"gs://{BUCKET_NAME}/translated_texts/{target_language}/"

    # speech_to_text_api
    language_code = payload["language_code"]  # "de_DE"
    gcs_uri_text_speech2text_result = f"gs://{BUCKET_NAME}/texts/{source_language}.txt"

    try:
        # Download YouTube video and upload to Cloud Storage
        video_path_local = helpers.download_youtube_video(link=youtube_link, video_filename=video_filename)

        helpers.upload_blob(bucket_name=BUCKET_NAME, source_file_name=video_path_local,
                            destination_blob_name=video_blob_name)

        process.process_video(PROJECT_ID=PROJECT_ID,
                              BUCKET_NAME=BUCKET_NAME,
                              video_path_local=video_path_local,
                              location=location,
                              language_code=language_code,
                              source_language=source_language,
                              target_language=target_language,
                              audio_filename=audio_filename,
                              gcs_uri_audio=gcs_uri_audio,
                              gcs_uri_text_speech2text_result=gcs_uri_text_speech2text_result,
                              gcs_uri_text_translation_result=gcs_uri_text_translation_result)

        response = "Success"

        return Response(response, status=200, headers=response_headers)

    except Exception as error:
        msg = "Failed to extract the message length. Error: {}".format(error)
        logger.error(msg)
        return Response(msg, status=500, headers=response_headers)


@app.route("/video_file", methods=["POST"])
def video_file() -> Response:
    """
    Handle the video file endpoint.

    This function processes the video file specified in the payload and performs various operations on it,
    including downloading, audio extraction, speech-to-text conversion, translation, and subtitle generation.

    Example payload:
        payload = {
        "language_code": "de_DE",
        "source_language": "de",
        "target_language": "en"
        }

    Returns:
        Response: The response object with the status and headers.

    Raises:
        Exception: If an error occurs during the processing.

    """

    payload = request.get_json()

    # Check if all required fields are present - if not return error
    required_fields = ["language_code", "source_language", "target_language"]
    msg = helpers.check_payload_fields(required_fields, payload)
    if msg:
        return Response(msg, 400, response_headers)

    # video
    video_filename = "video.mp4"
    video_blob_name = f"videos/{video_filename}"
    gcs_uri_video = f"gs://{BUCKET_NAME}/{video_blob_name}"

    # audio
    audio_filename = "audio.wav"
    audio_blob_name = f"audios/{audio_filename}"
    gcs_uri_audio = f"gs://{BUCKET_NAME}/{audio_blob_name}"

    # translation_api
    source_language = payload["source_language"]  # de
    target_language = payload["target_language"]  # en
    gcs_uri_text_translation_result = f"gs://{BUCKET_NAME}/translated_texts/{target_language}/"

    # speech_to_text_api
    language_code = payload["language_code"]  # "de_DE"
    gcs_uri_text_speech2text_result = f"gs://{BUCKET_NAME}/texts/{source_language}.txt"

    try:
        # download file from cloud storage to current directory
        video_path_local = f"/Users/julius.haas/GCC_TryOuts/subtitle-generator/src/{video_filename}"
        helpers.download_blob(bucket_name=BUCKET_NAME,
                              source_blob_name=video_blob_name,
                              destination_file_name=video_path_local)

        process.process_video(PROJECT_ID=PROJECT_ID,
                              BUCKET_NAME=BUCKET_NAME,
                              video_path_local=video_path_local,
                              location=location,
                              language_code=language_code,
                              source_language=source_language,
                              target_language=target_language,
                              audio_filename=audio_filename,
                              gcs_uri_audio=gcs_uri_audio,
                              gcs_uri_text_speech2text_result=gcs_uri_text_speech2text_result,
                              gcs_uri_text_translation_result=gcs_uri_text_translation_result)

        response = "Success"

        return Response(response, status=200, headers=response_headers)

    except Exception as error:
        msg = "Failed to extract the message length. Error: {}".format(error)
        logger.error(msg)
        return Response(msg, status=500, headers=response_headers)


if __name__ == "__main__":
    """
    Start Flask in Cloud Run Container.
    """

    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        use_reloader=False,
    )
