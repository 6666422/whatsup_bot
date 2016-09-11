import json
import redis
import time
import initlogging

user_info_db = redis.StrictRedis(host='localhost', port=6379, db=1)
profile_to_user_db = redis.StrictRedis(host='localhost', port=6379, db=2)
LOG = initlogging.getlog(__name__)
current_time = lambda: int(time.time())

'''
UserInfo:
string state
Status[] statuses
Friends[] friends
string dp

Status :
string status
int64 ts

Friends :
stirng name
string app_id
'''


def read_statuses(ids):
    user_infos = [json.loads(info) for info in user_info_db.mget(ids) if info]

    user_infos = [(info['statuses'][-1], info['name']) for info in user_infos if
                  'statuses' in info and len(info['statuses']) != 0]
    user_infos.sort(key=lambda x: -x[0]['ts'])
    return user_infos


def add_status(user, status):
    pres = user_info_db.get(user)
    if not pres:
        pres = {}
    else:
        pres = json.loads(pres)
    if 'statuses' not in pres:
        pres['statuses'] = []
    pres['statuses'].append({'status': status, 'ts': current_time()})
    user_info_db.set(user, json.dumps(pres))


def get_user_info(user):
    return json.loads(user_info_db.get(user))


def normalize_dp(dp):
    return dp.split('/')[-1].split('.')[0]


def get_empty_if_ne(client, key, default={}):
    ret = client.get(key)
    if ret:
        LOG.info("===={}===".format(ret))
        return json.loads(ret)
    return default


def get_profile(user):
    ui = get_empty_if_ne(user_info_db, user)
    fields = ['profile_pic', 'first_name', 'last_name']
    return {field: ui[field] for field in fields if field in ui}


def set_name(user, name):
    ui = get_empty_if_ne(user_info_db, user)
    ui['name'] = name
    user_info_db.set(user, json.dumps(ui))


def set_profile(user, profile):
    pres = user_info_db.get(user)
    if not pres:
        pres = {}
    else:
        pres = json.loads(pres)
    profile['profile_pic'] = normalize_dp(profile['profile_pic'])
    pres.update(profile)
    user_info_db.set(user, json.dumps(pres))
    
    comp_key = '{}_{}_{}'.format(
        profile['profile_pic'], profile['first_name'], profile['last_name'])
    pres_ids = set(get_empty_if_ne(profile_to_user_db, comp_key, default=[]))
    pres_ids.add(user)
    profile_to_user_db.set(comp_key, json.dumps(list(pres_ids)))


def set_app_friends(user, friends):
    friends = [{'app_id': f['id'], 'name': f['name']} for f in friends]
    LOG.info(friends)
    ui = get_empty_if_ne(user_info_db, user)
    ui['friends'] = friends
    LOG.info(ui)
    user_info_db.set(user, json.dumps(ui))


def add_friend(user, friend):
    ui = get_empty_if_ne(user_info_db, user)
    user_friends = ui.get('friends', [])
    friend_ids = {fr['app_id'] for fr in user_friends}
    if friend['app_id'] in friend_ids:
        return
    user_friends.append(friend)
    ui['friends'] = user_friends
    user_info_db.set(user, json.dumps(ui))


# friends : in fb's response format
# This will not have app_id, will have id
def update_friends_profiles(user_name, user_id, friends):
    to_add = {'app_id': user_id, 'name': user_name}
    for friend in friends:
        add_friend(friend['id'], to_add)


def get_app_friends(app_user):
    ui = get_empty_if_ne(user_info_db, app_user)
    return ui.get('friends', [])


def users_from_profile(profile):
    profile['profile_pic'] = normalize_dp(profile['profile_pic'])
    comp_key = '{}_{}_{}'.format(
        profile['profile_pic'], profile['first_name'], profile['last_name']) 
    ret = profile_to_user_db.get(comp_key)
    if ret:
        return json.loads(ret)
    return []


def set_user_extras(user, extra):
    ui = get_empty_if_ne(user_info_db, user)
    ui.update(extra)
    user_info_db.set(user, json.dumps(ui))


def set_state(user, state):
    ui = get_empty_if_ne(user_info_db, user)
    ui['state'] = state
    user_info_db.set(user, json.dumps(ui))

def reset_state(user):
    ui = get_empty_if_ne(user_info_db, user)
    del ui['state']
    user_info_db.set(user, json.dumps(ui))


def get_state(user):
    ui = get_empty_if_ne(user_info_db, user)
    return ui.get('state', None)

if __name__ == '__main__':
    while True:
        user = raw_input()
        add_status(user, raw_input())
        print read_statuses(raw_input().split(' '))
