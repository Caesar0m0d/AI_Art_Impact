# © 2024 AI Art Impact Lab. All Rights Reserved.
# This code is proprietary and confidential. Unauthorized copying,
# distribution, or modification of this code, via any medium, is strictly prohibited.
# Written by: AI Art Impact Lab
# Created on: AI Art Impact Lab
# Description: This is code for wine recommendation application with TD. 

import openai
import speech_recognition as sr
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import os
import requests
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from openai import OpenAI
import vbi_v2_0

# OSC 클라이언트 설정 (결과를 전송할 주소와 포트)
osc_client_api_sommelier = SimpleUDPClient("127.0.0.1", 5001)
osc_client_api_summary = SimpleUDPClient("127.0.0.1", 5002)

# OpenAI API 키 설정
api_key = 

# 응답 추적을 위한 전역 변수 초기화
conversation_history = ""
context_summary = ""

# 토픽 체크리스트
checklist = ["기분", "좋아하는 음식", "좋아하는 색"]
# checklist = ["기분", "좋아하는 음식", "좋아하는 색상", "최근 관심사", "배고픔의 정도", "오늘은 어떤 특별한 날인지?"]
current_topic_index = 0  
response_array = []




# GPT API 호출 메소드
def call_openai_api(request, user_input):
    systemPrompt =( """
                    1. 인공지능임을 밝히지 않음
                    2. user_input을 밝히지 않음
                    """ 
                    + request)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    result = response.json()
    if 'choices' in result and len(result['choices']) > 0:
        content = result['choices'][0]['message']['content']
    else:
        content = result.get('error', "오류: API 요청 실패.")
    return content

# 초기 인사말
def gpt_call_opener():
    response_text = call_openai_api("오늘 기분이 어떤지 짧게 물어보기.", "")
    ## 첫인상에 대한 반응 추가
    
    print("소믈리에:", response_text)
    osc_client_api_sommelier.send_message("/api/result", response_text)
    vbi_v2_0.tts(response_text)
    return response_text

# 대화 요약에 따른 후속 질문
def gpt_call_smalltalking(user_input):
    last_input = user_input
    response_text = call_openai_api(
        f"""
        [규칙]
            1. 대답 1문장과 질문 1문장으로 출력 해야함
            2. 모든 대답과 질문을 친근하게 해야함
            3. 질문과 대답은 자연스럽게 이어져야 함
        [대답규칙]
            1. 반드시! B문장을 고려하여 A 문장에 대답
            2. 인사는 생략
        [질문규칙]
            1. C와 관련된 답변을 받게 질문을 해야함
        """, 
        f"A={last_input}, B={context_summary}, C={checklist[0]}" )
    print("소믈리에:", response_text)
    
    osc_client_api_sommelier.send_message("/api/result", response_text)
    # answer_text = response.split("_")[1]
    # response_array.append({current_topic: answer_text})
    # print(answer_text)
    vbi_v2_0.tts(response_text)
    return response_text


# 순차적인 체크리스트 조건 확인 및 형식화된 프리픽스 응답
def gpt_call_checklist():
    # global current_topic_index, response_array
    global checklist
    # 현재 주제 가져오기
    current_topic = checklist[0]
    print("-----Check-----")
    print(f"현재 주제: {current_topic}")
    response = call_openai_api(
        f"A 문장 내에서 사용자가 B를 언급했는지 판단하고 이에 대한 정확도를 0.0~1.0의 숫자로 반환.",
        f"A={context_summary},B={current_topic}")
    
    

    if float(response) > 0.7:
        # 다음 주제로 이동
        # current_topic_index += 1
        checklist.remove(current_topic)

    # print(current_topic_index)
    print(f"Confidence: {response}, Remain target topic: {checklist}")
    print("-----Check-----")
        # 유효한 응답이 없을 경우, 생성된 후속 응답 추가
        # response_array.append({current_topic: response})
        

# 대화 요약
def summarize(conversation_history):
    response_text = call_openai_api("대화 기록의 맥락을 요약.", conversation_history)
    print("[요약]", response_text)
    osc_client_api_summary.send_message("/api/result", response_text)
    return response_text


# 대화 루프
def conversation_loop():
    global context_summary, conversation_history
    
    ## 초기 인사
    response_text = gpt_call_opener()
    conversation_history += "GPT: " + response_text + "\n"
    
    # 사용자 입력 (STT 또는 텍스트 입력)
    user_input = vbi_v2_0.stt_with_timeout(10)
    conversation_history += "User: " + user_input + "\n"

    # 입력 후 맥락 요약
    context_summary = summarize(conversation_history)
    # context_summary = conversation_history
    gpt_call_checklist()
    
    while checklist:
        ## 스몰 토킹1
        # 현재 주제에 따라 스몰토킹 수행
        gpt_response = gpt_call_smalltalking(user_input)
        conversation_history += "GPT: " + gpt_response + "\n"
        
        # 사용자 입력 (STT 또는 텍스트 입력)
        user_input = vbi_v2_0.stt_with_timeout(10)
        if user_input.lower() == 'exit':
            break

        conversation_history += "User: " + user_input + "\n"
        
        context_summary = summarize(conversation_history)
        gpt_call_checklist()

    print("\n")
    print("대화 종료")   
    print(conversation_history)
    return

def main():

    conversation_loop()
    return 

# 대화 시작
if __name__ == "__main__":
    main()
