from flask import Flask, render_template, request, redirect, session
import requests
import logging
from .context import ContextCreator
import json


app = Flask(__name__)
context_creator = ContextCreator()


@app.route('/prompt', methods=['POST'])
def handle_post():
    if request.method == 'POST':
        json_req = request.json
        user_prompt = extract_prompt_context(request)
        dynamic_context = context_creator.retrieve(user_prompt)
        mod_request = add_dynamic_context(request, dynamic_context)
        res = forward_request(mod_request, "http://127.0.0.1:8081/v1/chat/completions")
        return res.json()
    return "Only POST requests supported", 400

def forward_request(request, url):
    res = requests.post(url=url, headers=request.headers, json=request.json)
    return res

def extract_prompt_context(request):
    content = json.loads(request.json['messages'][1]['content'])
    prompt_context = json.loads(content['context'])['prompt context']
    prompt_context.append({'user prompt': content['user prompt']})
    return json.dumps(prompt_context)


def add_dynamic_context(request, dynamic_context):
    content_str = request.json['messages'][1]['content']
    mod_content_str = content_str + dynamic_context
    req_json = request.json['messages'][1]['content'] = mod_content_str
    return request
