import os
from dotenv import load_dotenv
import openai
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
import tempfile
import playsound
import time
import queue

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

samplerate = 16000
threshold = 0.03
silence_duration = 1.0
block_duration = 0.1
channels = 1

audio_q = queue.Queue()
speaking = False
silence_start = None

def audio_callback(indata, frames, time_info, status):
    global speaking, silence_start

    volume_norm = np.linalg.norm(indata)

    if speaking:
        audio_q.put(indata.copy())

        if volume_norm < threshold:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start > silence_duration:
                raise sd.CallbackStop()
        else:
            silence_start = None
    else:
        if volume_norm > threshold:
            print("말 시작 감지")
            speaking = True
            audio_q.put(indata.copy())

def listen_and_record():
    global speaking, silence_start
    speaking = False
    silence_start = None
    audio_frames = []

    with sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=channels, blocksize=int(samplerate * block_duration)):
        print("🟢 마이크 ON (Listening)")

        while not speaking:
            time.sleep(0.01)

        try:
            while True:
                frame = audio_q.get(timeout=1.0)
                audio_frames.append(frame)
        except queue.Empty:
            print("🔴 말 끝 감지. 녹음 종료.")

    if audio_frames:
        recording = np.concatenate(audio_frames, axis=0)
        return recording
    else:
        return None


def transcribe_recording(recording, samplerate=16000):
    if recording is None:
        print("❗ 녹음 데이터가 없습니다.")
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        scipy.io.wavfile.write(temp_wav.name, samplerate, recording)

        with open(temp_wav.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            text = transcript.text
            print(f"📝 인식된 텍스트: {text}")
            return text

def gpt4_response(prompt_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 친절하고 자연스러운 키오스크 비서야."},
                {"role": "user", "content": prompt_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[GPT-4 응답 에러] {e}")
        return None

def speak_with_openai_tts(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        temp_filename = f"response_{time.time()}.mp3"
        with open(temp_filename, "wb") as f:
            f.write(response.content)
        
        playsound.playsound(temp_filename)
        os.remove(temp_filename)
    except Exception as e:
        print(f"[TTS 출력 에러] {e}")

def main():
    recording = listen_and_record()

    if recording is None:
        print("녹음 실패. 다시 대기합니다.\n")
        return None

    stt_text = transcribe_recording(recording)

    if stt_text is None:
        print("인식 실패. 다시 대기합니다.\n")
        return None

    print(f"인식된 텍스트: {stt_text}")

    print("GPT-4 응답 생성 중...")
    gpt_reply = gpt4_response(stt_text)

    if gpt_reply is None:
        print("대답 생성 실패.")
        return stt_text  # 텍스트는 반환

    print(f"키오스크 응답: {gpt_reply}")

    print("답변 음성 출력 중...")
    speak_with_openai_tts(gpt_reply)

    return stt_text


if __name__ == "__main__":
    main()