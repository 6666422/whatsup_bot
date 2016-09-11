import json
import logging
import random
import urllib

from flask import Flask, request, Response

import messenger_utils
import dbhelper
from initlogging import handler, print_exc

app = Flask(__name__)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
LOG = app.logger
LOG.print_exc = lambda msg: print_exc(LOG, msg)
LOG.info("log started")


@app.route('/')
@app.route('/index')
def index_handler():
    return 'Im alive'


# Load balancer health page
@app.route('/health')
def health_handler():
    return 'yes'


def mid_to_aid(mid):
    LOG.info('+++++++++++++in mid to aid++++++++++++')
    profile = dbhelper.get_profile(mid)
    if not profile:
        profile = messenger_utils.request_profile_as_page(mid)
        dbhelper.set_profile(mid, profile)
    users = set(dbhelper.users_from_profile(profile))
    users.remove(mid)
    users = list(users)
    if users == []:
        return None, 'NO_LOGIN'
    return users[0], 'NP'


@app.route('/whatsup/hookup', methods=['POST', 'GET'])
def messenger():
    query = request.form.copy()
    query.update(request.args)
    LOG.info(query)
    LOG.info(request.data)
    try:
        challenge = messenger_utils.check_challenge()
        if challenge:
            LOG.info(":/")
            LOG.info(challenge)
            return challenge
        text_and_users = messenger_utils.get_messenger_text_and_users()
        LOG.info("==" + str(text_and_users))
        for msg in text_and_users:
            sender = msg['sender']
            if 'msg' not in msg and 'postback' not in msg:
                continue
            aid, _ = mid_to_aid(sender['id'])
            LOG.info(aid)
            LOG.info(msg)
            if not aid:
                messenger_utils.send_reply(
                    sender, 'login here: https://yesteapea.com/facebooklogin.html')
            else:
                if 'msg' in msg and dbhelper.get_state(aid) == 'UPDATE':
                    dbhelper.add_status(aid, msg['msg'])
                    dbhelper.reset_state(aid)
                elif 'postback' in msg and msg['postback'] == 'UPDATE_STATUS':
                    dbhelper.set_state(aid, 'UPDATE')
                    messenger_utils.send_reply(
                        sender, 'Awesome, Enter your update')
                elif 'postback' in msg and msg['postback'] == 'FRIEND_FEED':
                    friends = [m['app_id'] for m in
                               dbhelper.get_app_friends(aid)]
                    for status, user in dbhelper.read_statuses(friends):
                        messenger_utils.send_reply(
                            sender, '{} - {}'.format(status['status'], user))
                else:
                    frs = dbhelper.get_app_friends(aid)
                    messenger_utils.send_reply(
                        sender, '\n'.join([fr['name'] for fr in frs]))
    except Exception:
        LOG.print_exc("messenger fail")
    return Response()


@app.route('/whatsup/appflow', methods=['POST', 'GET'])
def appflow():
    query = request.form.copy()
    query.update(request.args)
    LOG.info(query)
    profile = json.loads(query['profile'])
    dbhelper.set_profile(query['user'],
                         {'profile_pic': profile['picture']['data']['url'],
                          'first_name': profile['first_name'],
                          'last_name': profile['last_name']})
    dbhelper.set_user_extras(query['user'],
                             {'is_app': True,
                              'name': profile['name']})
    friends = json.loads(query['friends'])['data']
    dbhelper.set_app_friends(query['user'], friends)
    dbhelper.update_friends_profiles(profile['name'], query['user'], friends)

    return Response()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8582)
