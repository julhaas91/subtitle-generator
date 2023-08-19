# Subtitle Generator

Subtitle Generator is a Python application that allows you to generate subtitles for videos.
It utilizes Google Cloud Speech-to-Text API and Translate API, as well as Cloud Storage and
-if deployed as a service- Cloud Run.

The Subtitle Generator downloads a given video, splits the audio from the video and utilizes
Google Cloud Speech-to-Text API and Google Translate API, as well as custom functionality to create SRT files in the
specified languages.

## Prerequisites

Before using the Subtitle Generator, make sure you have the following installed:

- Python 3.9
- Google Cloud account and credentials
- FFmpeg

## Local Installation

1. Clone the repository:
   ```git clone https://github.com/your-username/subtitle-generator.git```
2. Create a virtual environment:
   ```./Taskfile.sh create subtitle-generator python=3.9```
3. Activate the virtual environment:
   ```conda activate subtitle-generator```
4. Install the required Python dependencies:
   ```./Taskfile.sh install-local```
5. Set up your Google Cloud credentials by following the [official documentation](https://cloud.google.com/docs/authentication/getting-started).
6. Make sure FFmpeg is installed and accessible from the command line. You can download FFmpeg from the [official website](https://ffmpeg.org/).
7. Specify the variables ```PROJECT_ID``` and ```BUCKET_NAME``` in the ```main.py``` file.

## Local Usage

The subtitle generator supports two options for input: You can either provide a YouTube link or upload a *.mp4 video file
to the `/videos`-folder of the cloud storage bucket. Make sure to create a cloud storage bucket in your Google Cloud project
and to set the environment variables accordingly.

Then run the Subtitle Generator with the following command: ```./Taskfile.sh```

Find example request payloads for each of the routes below. Note that the parameter `language_code` refers to the
language for the Speech-to-Text API and the parameters `source_language` and `target_language` refer to the Translate API.

See the list of all possible languages for the Speech-to-Text API [here](https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages) and the list of all possible languages for the Translation API [here](https://cloud.google.com/translate/docs/languages).

### Youtube link:

Send POST requests to:
```http://localhost:5000/youtube```

#### Example request for the youtube route:

```json
{
    "link": "https://www.youtube.com/watch?v=XJNO492juTE",
    "language_code": "de_DE",
    "source_language": "de",
    "target_language": "en"
}
```

### Video file:

Prepare your input video file and make sure it meets the requirements supported by FFmpeg.

Send POST requests to:
```http://localhost:5000/video```

#### Example request for the video route:

```json
{
    "language_code": "de_DE",
    "source_language": "de",
    "target_language": "en"
}
```

After the process is complete, the generated subtitles will be saved as an SRT file in the specified Cloud Storage bucket.

## Cloud Deployment with Cloud Run

Create a service account with sufficient rights [create service accounts](https://cloud.google.com/iam/docs/service-accounts-create).

Set the project and service account variables in the ```./Taskfile.sh```.

Deploy the application as a Cloud run service:
```./Taskfile.sh deploy```

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please create an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
