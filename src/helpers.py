from typing import Tuple, List
import os
import pytube
import srt
from pydub.utils import mediainfo
import subprocess

from google.cloud import storage
from src.common import logger

from dotenv import load_dotenv

# load env vars
load_dotenv()
BUCKET_NAME = os.getenv("BUCKET_NAME")


def check_payload_fields(expected_fields: list, payload: dict) -> str:
    """
    This function checks if all expected fields are present in the payload.
    :param expected_fields:
    :param payload:
    :return:
    """

    for param in expected_fields:
        if param not in payload:
            msg = f"Required field {param} is missing in request. Request needs parameters {expected_fields}"
            logger.error(msg)
            return msg

    # if all required fields are present, return empty string
    return ""


def upload_blob(bucket_name: str, source_file_name: str, destination_blob_name: str) -> None:
    """
    Uploads a file to the specified bucket.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_file_name (str): The local path to the file to upload.
        destination_blob_name (str): The name to give to the uploaded blob.

    Returns:
        None

    Raises:
        Exception: If there is an error in uploading the file.

    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


def download_blob(bucket_name: str, source_blob_name: str, destination_file_name: str) -> None:
    """
    Downloads a blob from the specified bucket.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_blob_name (str): The name of the blob to download.
        destination_file_name (str): The local path where the file should be saved.

    Returns:
        None

    Raises:
        Exception: If there is an error in downloading the blob.

    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Construct a client-side representation of the blob
    blob = bucket.blob(source_blob_name)

    # Download the blob to the specified destination file
    blob.download_to_filename(destination_file_name)

    print(
        f"Downloaded storage object {source_blob_name} from bucket {bucket_name} to local file {destination_file_name}.")


def download_blob_to_text_file(bucket_name: str, source_blob_name: str) -> str:
    """
    Downloads a blob from the specified bucket and returns its contents as text.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_blob_name (str): The name of the blob to download.

    Returns:
        str: The contents of the downloaded blob as text.

    Raises:
        Exception: If there is an error in downloading the blob.

    """
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client-side representation of the blob
    blob = bucket.blob(source_blob_name)

    # Download the blob contents as text
    file_contents = blob.download_as_text()

    return file_contents


def download_youtube_video(link: str, video_filename: str) -> str:
    """
    Download a YouTube video given its link and rename the downloaded file.

    Args:
        link (str): The YouTube video link.
        video_filename (str): The desired filename for the downloaded video.

    Returns:
        str: The local path of the renamed video file.

    Raises:
        Exception: If there is an error in downloading or renaming the video.

    """
    try:
        # Create a YouTube object using the provided link
        yt = pytube.YouTube(link)
    except:
        print("Connection Error")  # Handle connection exception

    # Download the video with the highest resolution in mp4 format
    video_path = yt.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first().download()

    # Rename the downloaded video file
    new_path_local = video_path.split('/')
    new_filename = video_filename
    new_path_local[-1] = new_filename
    new_path_local = '/'.join(new_path_local)
    os.rename(video_path, new_path_local)

    return new_path_local


def get_video_info(video_filepath: str) -> Tuple[int, int, int]:
    """
    Retrieve the number of channels, bit rate, and sample rate of a video file.

    Args:
        video_filepath (str): The path to the video file.

    Returns:
        Tuple[int, int, int]: A tuple containing the number of channels, bit rate, and sample rate.

    Raises:
        Exception: If there is an error in retrieving the video information.

    """
    # Retrieve video information using mediainfo tool
    video_data = mediainfo(video_filepath)

    # Extract required information
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate


def video_to_audio(video_filepath: str, audio_filename: str, video_channels: int, video_bit_rate: str,
                   video_sample_rate: int) -> str:
    """
    Converts a video file to an audio file and uploads it to Cloud Storage.

    Args:
        video_filepath (str): The filepath of the video file.
        audio_filename (str): The filename of the output audio file.
        video_channels (int): The number of audio channels in the video.
        video_bit_rate (str): The desired audio bit rate of the output audio file.
        video_sample_rate (int): The desired audio sample rate of the output audio file.

    In the ffmpeg command, the arguments have the following meanings:
        -i {video_filepath}: Specifies the input video
            file path.
        -b:a {video_bit_rate}: Sets the audio bit rate for the output audio file. The {video_bit_rate}
            placeholder should be replaced with the desired bit rate value, specified in kilobits per second (e.g.,
            "128k").
        -ac {video_channels}: Sets the number of audio channels for the output audio file. The {video_channels}
            placeholder should be replaced with the desired number of channels.
        -ar {video_sample_rate}: Sets the audio sample rate for the output audio file, specified in hertz (Hz).
            The {video_sample_rate} placeholder should be replaced with the desired sample rate value.
        -vn: Disables video recording, indicating that only the audio should be processed. {audio_filename}: Specifies
            the output audio file name. -y: Automatically overwrites the output file if it already exists without
            prompting for confirmation.

    Returns:
        str: The GCS URI of the uploaded audio file.
    """
    command = f"ffmpeg -i {video_filepath} -b:a {video_bit_rate} -ac {video_channels} -ar {video_sample_rate} -vn {audio_filename} -y"
    subprocess.call(command, shell=True)
    blob_name = f"audios/{audio_filename}"
    upload_blob(BUCKET_NAME, audio_filename, blob_name)
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"

    return gcs_uri


def write_srt(bucket_name: str, subtitles: List[srt.Subtitle], language: str = "de") -> None:
    """
    Write subtitles to an SRT file and upload it to Google Cloud Storage.

    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket.
        subtitles (List[srt.Subtitle]): The list of subtitle objects.
        language (str, optional): The language code for the subtitles. Defaults to "de".

    Returns:
        None
    """
    # Write locally
    srt_file = f"{language}.srt"
    print(f"Writing {language} subtitles to: {srt_file}")
    with open(srt_file, 'w', encoding="utf-8") as f:
        f.writelines(srt.compose(subtitles))

    # Upload to Google Cloud Storage
    blob_name = f"subtitles/{language}.srt"
    upload_blob(bucket_name, srt_file, blob_name)

    # Clean up local file
    os.remove(srt_file)


def update_srt(original_subtitles: List[srt.Subtitle], translated_text: str) -> List[srt.Subtitle]:
    """
    Updates the content of original subtitles with the translated lines.

    Args:
        original_subtitles (List[srt.Subtitle]): The original subtitles.
        translated_text (str): The translated text.

    Returns:
        List[srt.Subtitle]: The updated original subtitles.
    """
    lines = translated_text.split("\n")
    i = 0
    # todo: Find a better way to handle the last line ('') instead of using [:-1].
    for line in lines[:-1]:
        original_subtitles[i].content = line
        i += 1
    return original_subtitles


def clean_up() -> None:
    """
    Deletes all files ending with *.wav, *.mp4, *.srt, and *.txt in the current directory.
    """
    extensions = (".wav", ".mp4", ".srt", ".txt")
    current_dir = os.getcwd()

    for file in os.listdir(current_dir):
        if file.endswith(extensions):
            file_path = os.path.join(current_dir, file)
            os.remove(file_path)
