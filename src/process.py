from typing import List
from google.cloud import speech, translate
from time import sleep
import srt
from src import helpers


def process_video(PROJECT_ID: str, BUCKET_NAME: str, video_path_local: str, location: str, language_code: str,
                  source_language: str, target_language: str, audio_filename: str, gcs_uri_audio: str,
                  gcs_uri_text_speech2text_result: str, gcs_uri_text_translation_result: str) -> None:
    """
    Process the video by performing speech-to-text transcription, translation, and generating subtitles.

    Args:
        PROJECT_ID (str): The project ID.
        BUCKET_NAME (str): The name of the Cloud Storage bucket.
        video_path_local (str): The local path of the video file.
        location (str): The location.
        language_code (str): The language code for speech recognition.
        source_language (str): The source language for translation.
        target_language (str): The target language for translation.
        audio_filename (str): The filename of the audio file.
        gcs_uri_audio (str): The GCS URI of the audio file.
        gcs_uri_text_speech2text_result (str): The GCS URI of the speech-to-text result.
        gcs_uri_text_translation_result (str): The GCS URI of the translation result.

    """
    channels, bit_rate, sample_rate = helpers.get_video_info(video_path_local)

    gcs_uri = helpers.video_to_audio(video_path_local, audio_filename, channels, bit_rate, sample_rate)
    assert gcs_uri == gcs_uri_audio

    subtitles = long_running_recognize(gcs_uri_audio, language_code, channels, sample_rate)

    helpers.write_srt(bucket_name=BUCKET_NAME, subtitles=subtitles, language=source_language)
    helpers.write_txt(bucket_name=BUCKET_NAME, subtitles=subtitles, language=source_language)

    batch_translate_text(input_uri=gcs_uri_text_speech2text_result,
                         output_uri=gcs_uri_text_translation_result,
                         project_id=PROJECT_ID,
                         location=location,
                         source_language=source_language,
                         target_language=target_language)

    translated_text = helpers.download_blob_to_text_file(bucket_name=BUCKET_NAME,
                                                         source_blob_name=f"translated_texts/{target_language}/subtitle-generator-bucket_texts_{source_language}_{target_language}_translations.txt")

    helpers.update_srt(original_subtitles=subtitles, translated_text=translated_text)
    helpers.write_srt(bucket_name=BUCKET_NAME, subtitles=subtitles, language=target_language)

    helpers.clean_up()


# SPEECH-TO-SRT
def long_running_recognize(gcs_uri: str, language_code: str, channels: int, sample_rate: int) -> List[srt.Subtitle]:
    """
    Perform long running speech recognition on the audio file.

    Args:
        gcs_uri (str): The GCS URI of the audio file.
        language_code (str): The language code for speech recognition.
        channels (int): The number of audio channels.
        sample_rate (int): The sample rate of the audio.

    Returns:
        List[srt.Subtitle]: The list of generated subtitles.

    """
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        language_code=language_code,
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=int(sample_rate),
        audio_channel_count=int(channels),
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True
    )
    audio = speech.RecognitionAudio(uri=gcs_uri)

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result()

    subs = []

    for result in response.results:
        # First alternative is the most probable result
        subs = break_sentences(subs, result.alternatives[0])

    print("Transcribing finished")
    return subs


def break_sentences(subs: List[srt.Subtitle], alternative) -> List[srt.Subtitle]:
    """
    Break the sentences based on word boundaries and punctuation marks.

    Args:
        subs (List[srt.Subtitle]): The list of subtitles.
        alternative: The speech recognition alternative.

    Returns:
        List[srt.Subtitle]: The updated list of subtitles.

    """
    firstword = True
    max_chars = 40
    charcount = 0
    idx = len(subs) + 1
    content = ""

    for w in alternative.words:
        if firstword:
            # first word in sentence, record start time
            start = w.start_time

        charcount += len(w.word)
        content += " " + w.word.strip()

        if ("." in w.word or "!" in w.word or "?" in w.word or
                charcount > max_chars or
                ("," in w.word and not firstword)):
            # break sentence at: . ! ? or line length exceeded
            # also break if , and not first word
            subs.append(srt.Subtitle(
                index=idx,
                start=start,
                end=w.end_time,
                content=srt.make_legal_content(content)
            ))
            firstword = True
            idx += 1
            content = ""
            charcount = 0
        else:
            firstword = False

    return subs


# TRANSLATE-TXT
def get_supported_languages(PROJECT_ID: str, location: str) -> None:
    """
    Get a list of supported language codes.

    Args:
        PROJECT_ID (str): The project ID.
        location (str): The location.

    Returns:
        None

    """
    client = translate.TranslationServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{location}"
    response = client.get_supported_languages(parent=parent)

    # List language codes of supported languages
    print('Supported Languages: ', end='')
    for language in response.languages:
        print(u"{} ".format(language.language_code), end='')
    print("\n")


def batch_translate_text(input_uri: str, output_uri: str, project_id: str, location: str, source_language: str, target_language: str) -> None:
    """
    Perform batch translation of text.

    Args:
        input_uri (str): The input URI specifying the source text file.
        output_uri (str): The output URI specifying the destination for translated text.
        project_id (str): The project ID.
        location (str): The location.
        source_language (str): The source language code.
        target_language (str): The target language code(s).

    Returns:
        None

    """
    client = translate.TranslationServiceClient()

    target_language_codes = target_language.split(",")
    gcs_source = {"input_uri": input_uri}
    mime_type = "text/plain"
    input_configs_element = {"gcs_source": gcs_source, "mime_type": mime_type}
    input_configs = [input_configs_element]
    gcs_destination = {"output_uri_prefix": output_uri}
    output_config = {"gcs_destination": gcs_destination}
    parent = f"projects/{project_id}/locations/{location}"

    operation = client.batch_translate_text(
        request={
            "parent": parent,
            "source_language_code": source_language,
            "target_language_codes": target_language_codes,
            "input_configs": input_configs,
            "output_config": output_config,
        }
    )

    # Initial delay
    total_wait_secs = 60
    print(f"Waiting for operation to complete... {total_wait_secs:.0f} secs")

    delay_secs = 10
    sleep(total_wait_secs)
    while not operation.done():
        # Exponential backoff
        delay_secs *= 1.1
        total_wait_secs += delay_secs
        print(f"Checking again in: {delay_secs:.0f} seconds | total wait: {total_wait_secs:.0f} secs")
        sleep(delay_secs)

    response = operation.result()
    print(u"Total Characters: {}".format(response.total_characters))
    print(u"Translated Characters: {}".format(response.translated_characters))
