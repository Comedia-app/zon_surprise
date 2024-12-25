import streamlit as st
from openai import OpenAI
import pandas as pd
import numpy as np
import os
import time
import base64
import io

OPENAI_API_KEY= st.secrets["api_key"]

client = OpenAI(api_key=OPENAI_API_KEY)

def assistantCreation(assistant_name,instructions):
    model="gpt-4o"
    assistant = client.beta.assistants.create(instructions=instructions,model=model,name=assistant_name)
    return assistant.id
def threadCreation(prompt):
    messages = [{"role":"user", "content":prompt}]
    thread=client.beta.threads.create(messages=messages)
    return thread.id
def runAssistant(thread_id, assistant_id):
    run=client.beta.threads.runs.create(thread_id=thread_id,assistant_id=assistant_id)
    return run.id
def checkRunStatus(thread_id, run_id):
    run=client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run.status
def retrieveThread(thread_id):
    thread_messages=client.beta.threads.messages.list(thread_id)
    thread_list=thread_messages.data
    assistant_message=thread_list[0]
    #reference=assistant_message.content[0].text.annotations.file_citation.quote
    message_text=assistant_message.content[0].text.value
    return message_text#, reference
def addMessageToThread(thread_id, prompt):
    thread_message= client.beta.threads.messages.create(thread_id, role="user",content=prompt)

def run_a_prompt_first(assistant_name, instructions, prompt):
    assistant_id=assistantCreation(assistant_name,instructions)
    thread_id=threadCreation(prompt)
    run_id=runAssistant(thread_id, assistant_id)
    run_status=checkRunStatus(thread_id, run_id)
    while run_status != 'completed':
        time.sleep(1)
        run_status=checkRunStatus(thread_id, run_id)
        if run_status=='failed':
            print(run_status)
        else:
            pass
    message_text =retrieveThread(thread_id)
    return message_text, thread_id, assistant_id

def run_a_prompt_second(thread_id, prompt2, assistant_id):
    addMessageToThread(thread_id, prompt2)
    run_id=runAssistant(thread_id, assistant_id)
    run_status=checkRunStatus(thread_id, run_id)
    while run_status != 'completed':
        time.sleep(1)
        run_status=checkRunStatus(thread_id, run_id)
        if run_status=='failed':
            print(run_status+"will try again")
            
        else:
            pass
    message_text2 =retrieveThread(thread_id)
    return message_text2, thread_id, assistant_id

def encode_image(file):
    # Read the content of the file-like object and encode it
    return base64.b64encode(file.read()).decode('utf-8')

def get_info_image(base64_image):

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
        {
            "role": "user",
            "content": [
            {"type": "text", "text": "Dit is een nederlands talige GPT waar je foto's naar kan uploaden, deze foto's worden vervolgens beschreven in een uitgebreid verslag en interpetatie die humorvol en vlot is. Je let vooral op cinamatogragfische inderdelen en bent ook critisch. De GPT output maximaal 300 tokens"},
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "high",
                },
            },
            ],
        }
        ],
        max_tokens=800,
    )
    message=response.choices[0].message.content
    return message

def make_speech_file_host(Text_in_speech):
    response= client.audio.speech.create(
        model='tts-1-hd',
        voice='onyx',
        input=Text_in_speech,
    )
    # audio_data = io.BytesIO()
    # response.stream_to_file(audio_data)
    audio_data = io.BytesIO()
    for chunk in response.iter_bytes():
        audio_data.write(chunk)
    audio_data.seek(0)
    return audio_data
    
def image_to_text(image_path):
    base64_image= encode_image(image_path)
    message=get_info_image(base64_image)
    return message

st.set_page_config(layout='wide')

with open(f'instructions.txt', 'r') as file:
    # Read the contents of the file
    instructions = file.read()
assistant_name='Chivo de cinematograaf'

picture = st.camera_input(".")

if picture:
    with st.spinner('Wait for it...'):
        prompt=image_to_text(picture)
        if 'run_num' in st.session_state:
            st.session_state.message_text, st.session_state.thread_id, st.session_state.assistant_id = run_a_prompt_second(st.session_state.thread_id, prompt, st.session_state.assistant_id)
            st.text('tweede foto')
        else: 
            st.text('eerste foto')
            st.session_state.message_text, st.session_state.thread_id, st.session_state.assistant_id=run_a_prompt_first(assistant_name, instructions, prompt)
            st.session_state.run_num='value'
        # st.text(test)
        audio_data=make_speech_file_host(st.session_state.message_text)
    st.audio(audio_data, autoplay=True)
