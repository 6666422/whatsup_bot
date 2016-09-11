import json

import requests
from flask import request, Response

from initlogging import getlog
from utils import read_file

LOG = getlog(__name__)
# disk ftw :/
messenger_secret = read_file('/usr/local/whatsup_secret', prefix="")
page_access_token = read_file('/usr/local/whatsup_token', prefix="")
LOG.info(messenger_secret)
LOG.info(page_access_token)


def check_challenge():
    query = request.form.copy()
    query.update(request.args)
    mode = query.get('hub.mode', 'FAIL')
    verify = query.get('hub.verify_token', 'FAIL')
    if mode == 'subscribe' and verify == messenger_secret:
        return Response(query['hub.challenge'])
    return None


def request_profile_as_page(user):
    r = requests.get('https://graph.facebook.com/v2.7/' + user,
                     params={
                         'access_token': page_access_token,
                         'fields': 'profile_pic,first_name,last_name'})
    LOG.info(r.json())
    return r.json()


def get_messenger_text_and_users():
    data = json.loads(request.data)
    entries = data['entry']
    LOG.info(entries)
    ret = []
    for entry in entries:
        msg0 = entry['messaging'][0]
        clean = {'sender': msg0['sender']}
        if 'message' in msg0:
            if msg0.get('is_echo', False):
                continue
            clean['msg'] = msg0['message']['text'].lower().strip()
            ret.append(clean)
        elif 'postback' in msg0:
            clean['postback'] = msg0['postback']['payload']
            ret.append(clean)
    LOG.info(ret)
    return ret


def send_reply(recipient, text):
    pat = page_access_token
    msg = {'recipient': recipient, 'message': {'text': text}}
    r = requests.post('https://graph.facebook.com/v2.6/me/messages',
                      params={'access_token': pat}, json=msg)
    LOG.info(r.json())
