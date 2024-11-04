
#voice based interface, VBI

import os
import io
import threading
import speech_recognition as sr
from openai import OpenAI
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import time

api_key = "sk-_UGFDmwnP9PmNPBsYtJoilBo_hTQEWUe1Nlekh8q8OT3BlbkFJetTNA5d2ou0HIcYN9e5qYvvdKgVr_IkAqdDy8EcT4A"

# 음성 인식 (STT)와 동시에 텍스트 입력 옵션 제공
def stt_with_timeout(timeout=10):
    user_text = ""
    stop_listening = threading.Event()
    
    # 음성 듣기 기능
    def listen():
        nonlocal user_text
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("말씀해 주세요 :")
            audio = recognizer.listen(source, phrase_time_limit=timeout)
        try:
            user_text = recognizer.recognize_google(audio, language="ko-KR")
            print("사용자 발화:", user_text)
        except sr.UnknownValueError:
            print("음성을 이해하지 못했습니다.")
        except sr.RequestError as e:
            print(f"STT 요청 실패: {e}")

    # 음성 인식 스레드 시작
    listener_thread = threading.Thread(target=listen)
    listener_thread.start()
    
    # 텍스트 입력을 기다리는 동안 STT는 제한 시간 내 응답을 대기
    user_input = input("텍스트 입력: ")
    stop_listening.set()
    
    # STT 입력을 받았을 경우, 텍스트 입력을 무시하고 STT 결과를 반환
    return user_text if user_text else user_input

# 텍스트를 음성으로 변환 (TTS)
def tts(response_text, character="alloy"):
    client = OpenAI(api_key=api_key)
    

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=character,
            input=response_text
        )
        audio_stream = io.BytesIO(response.content)
        
        # pydub으로 메모리에서 오디오 로드 및 재생
        audio = AudioSegment.from_file(audio_stream, format="mp3")
        play(audio)
        
        audio_stream.close()
    
    except Exception as e:
        print(f"TTS 생성 실패: {e}")
