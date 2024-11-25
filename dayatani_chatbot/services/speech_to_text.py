import ffmpeg
import azure.cognitiveservices.speech as speechsdk
import os
from chatbot.utils import remove_file


def __convert_to_wav(input_file_path):
    if not input_file_path or input_file_path.strip() == "":
        return None
    output_file_path = os.path.splitext(input_file_path)[0] + ".wav"

    stream = ffmpeg.input(input_file_path)
    stream = ffmpeg.output(stream, output_file_path)
    ffmpeg.run(stream, overwrite_output=True)
    return output_file_path


def convert_to_text(input_file_path):
    try:
        wav_audio_file_path = __convert_to_wav(input_file_path)
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
        )
        auto_detect_source_language_config = (
            speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["en-US", "id-ID", "hi-IN"]
            )
        )
        audio_config = speechsdk.AudioConfig(filename=wav_audio_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
        )

        result = speech_recognizer.recognize_once_async().get()
        print(f"AZURE SPEECH TO TEXT: {result}")
        remove_file(wav_audio_file_path)
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("details: {}".format(cancellation_details))
            print("Speech Recognition was canceled: {}".format(cancellation_details.reason))
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
        return result.text
    except Exception as e:
        print(e)
        return None
