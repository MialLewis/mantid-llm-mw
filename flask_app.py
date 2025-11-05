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
        user_prompt = extract_user_prompt(request)
        dynamic_context = context_creator.retrieve(user_prompt)
        logging.error(dynamic_context)
        mod_request = add_dynamic_context(request, dynamic_context)
        res = forward_request(mod_request, "http://127.0.0.1:8081/v1/chat/completions")
        return res.json()
    return "Only POST requests supported", 400

def forward_request(request, url):
    res = requests.post(url=url, headers=request.headers, json=request.json)
    return res

def extract_user_prompt(request):
    content_str = request.json['messages'][1]['content']
    content = json.loads(content_str)
    return content['user prompt']


def add_dynamic_context(request, dynamic_context):
    context_str = request.json['messages'][1]['content']
    mod_context_str = context_str + dynamic_context
    req_json = request.json['messages'][1]['content'] = mod_context_str
    return request
