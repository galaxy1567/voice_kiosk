import os
import time
import queue
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile
import openai
import pygame
from dotenv import load_dotenv

# 환경 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

# 설정값
samplerate = 16000
threshold = 0.03
silence_blocks = 0
silence_blocks_threshold = 5
block_duration = 0.1
channels = 1

audio_q = queue.Queue()
speaking = False

# 대화 히스토리
chat_history = [
    {"role": "system", "content": "너는 친절하고 자연스럽게 대답하는 키오스크 비서야. 간결하고 빠르게 대답해."}
]

# 오디오 콜백
def audio_callback(indata, frames, time_info, status):
    global speaking, silence_blocks, silence_blocks_threshold

    volume_norm = np.linalg.norm(indata)

    if speaking:
        audio_q.put(indata.copy())
        if volume_norm < threshold:
            silence_blocks += 1
            if silence_blocks >= silence_blocks_threshold:
                raise sd.CallbackStop()
        else:
            silence_blocks = 0
    else:
        if volume_norm > threshold:
            speaking = True
            silence_blocks = 0
            audio_q.put(indata.copy())

# 무음 감지 녹음
def listen_and_record():
    global speaking, silence_blocks
    speaking = False
    silence_blocks = 0
    audio_frames = []

    with sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=channels, blocksize=int(samplerate * block_duration)):
        print("마이크 ON (Listening)")
        while not speaking:
            time.sleep(0.01)

        try:
            while True:
                frame = audio_q.get(timeout=1.0)
                audio_frames.append(frame)
        except queue.Empty:
            print("말 끝 감지, 녹음 종료")

    if audio_frames:
        recording = np.concatenate(audio_frames, axis=0)
        return recording
    else:
        return None

# Whisper STT 변환
def transcribe_recording(recording, samplerate=16000):
    if recording is None:
        print("녹음 데이터가 없습니다.")
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        scipy.io.wavfile.write(temp_wav.name, samplerate, recording)
        with open(temp_wav.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            text = transcript.text.strip()
            if not text:
                return None
            print(f"인식된 텍스트: {text}")
            return text

# GPT-4o 스트리밍 응답
def gpt4_response_with_history():
    try:
        stream_response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_history,
            stream=True
        )

        full_response = ""

        for chunk in stream_response:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                part = chunk.choices[0].delta.content
                print(part, end="", flush=True)
                full_response += part

        print()
        return full_response

    except Exception as e:
        print(f"GPT-4o 스트리밍 응답 에러: {e}")
        return None

# TTS 출력
def speak_with_openai_tts(client, text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        temp_filename = f"response_{time.time()}.mp3"
        with open(temp_filename, "wb") as f:
            f.write(response.content)

        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        os.remove(temp_filename)

    except Exception as e:
        print(f"TTS 출력 에러: {e}")

# 메인 루프
def main():
    global chat_history

    recording = listen_and_record()

    if recording is None:
        print("녹음 실패. 다시 대기합니다.")
        return None

    stt_text = transcribe_recording(recording)

    if stt_text is None:
        print("음성을 인식하지 못했습니다. 다시 말씀해 주세요.")
        speak_with_openai_tts(client, "죄송합니다, 다시 말씀해 주세요.")
        return None

    print(f"인식된 텍스트: {stt_text}")

    if "종료" in stt_text or "끝내자" in stt_text:
        return "종료"

    chat_history.append({"role": "user", "content": stt_text})

    print("GPT-4o 응답 생성 중...")
    gpt_reply = gpt4_response_with_history()

    if gpt_reply is None:
        print("대답 생성 실패.")
        return stt_text

    print(f"키오스크 응답: {gpt_reply}")

    chat_history.append({"role": "assistant", "content": gpt_reply})

    print("답변 음성 출력 중...")
    speak_with_openai_tts(client, gpt_reply)

    return stt_text
