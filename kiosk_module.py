import os
from dotenv import load_dotenv
import openai
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
import tempfile
import playsound

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=api_key)

def record_audio(duration = 5, samplerate = 16000):
    print('녹음시작')
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    return recording, samplerate

def save_wav(recording, samplerate):
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    scipy.io.wavfile.write(temp_wav.name, samplerate, recording)
    return temp_wav.name

def recognize_speech_openai(audio_path):
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model='whisper-1',file=audio_file)
        return transcript.text
    except Exception as e:
        print(f"[Whisper STT 에러] {e}")
        return None

def gpt4_response(prompt_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 친절한 키오스크 비서야"},
                {"role": "user", "content": prompt_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"GPT 응답 에러 {e}")
        return None

def speak_with_openai_tts(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        with open("response.mp3","wb") as f:
            f.write(response.content)
        playsound.playsound("response.mp3")
    except Exception as e:
        print(f"[TTS 출력 에러] {e}")

def main():
    recording, samplerate = record_audio(duration=5)
    audio_path = save_wav(recording, samplerate)
    print("인식중")
    stt_text = recognize_speech_openai(audio_path)
    if stt_text is None:
        print("음성인식 실패. 다시 시도해주세요.")
        return
    
    print(f"인식된 텍스트: {stt_text}")

    print("gpt 응답 생성중")
    gpt_reply = gpt4_response(stt_text)
    
    if gpt_reply is None:
        print("대답 생성 실패. 다시 시도해주세요")
        return stt_text

    print(f"키오스크 응답: {gpt_reply}")

    print("음성 출력중")
    speak_with_openai_tts(gpt_reply)

    return stt_text


if __name__ == "__main__":
    main()