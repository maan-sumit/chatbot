import azure.cognitiveservices.speech as speechsdk
import os
import uuid
import ffmpeg

def text_to_speech(text, dir_name):
    if not text or text.strip() == "":
        return None

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    temp_audio_file_path = os.path.join(dir_name, f"{uuid.uuid4()}.wav")
    output_audio_file_path = os.path.join(dir_name, f"{uuid.uuid4()}.mp3")

    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ["AZURE_SPEECH_KEY"],
        region=os.environ["AZURE_SPEECH_REGION"]
    )
    speech_config.speech_synthesis_voice_name = 'id-ID-ArdiNeural'

    audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_audio_file_path)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = speech_synthesizer.speak_text(text)

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Temporary audio content written to file '{temp_audio_file_path}'")

        # Convert the WAV file to MP3 using ffmpeg
        try:
            ffmpeg.input(temp_audio_file_path).output(output_audio_file_path, codec='libmp3lame').run(overwrite_output=True)
            print(f"Converted audio content written to file '{output_audio_file_path}'")
            os.remove(temp_audio_file_path)  # Remove the temporary WAV file
        except ffmpeg.Error as e:
            print(f"Error converting file: {e}")
            return None

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
        return None

    return output_audio_file_path