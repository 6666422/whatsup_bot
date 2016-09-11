import dbhelper
import sys
import json


def dedup(lst):
    s,ret = set(), []
    for fr in lst:
        if fr['app_id'] in s:
            continue
        s.add(fr['app_id'])
        ret.append(fr)
    return ret

f1, f2 = sys.argv[1], sys.argv[2]

c1 = dbhelper.get_empty_if_ne(dbhelper.user_info_db, f1)
c2 = dbhelper.get_empty_if_ne(dbhelper.user_info_db, f2)

if 'friends' not in c1 or type(c1['friends']) != list:
    c1['friends'] = []
if 'friends' not in c2 or type(c2['friends']) != list:
    c2['friends'] = []


print c1
print c2
c1['friends'].append({'name': 'Name1', 'app_id': f2})
c2['friends'].append({'name': 'Name1', 'app_id': f1})

c1['friends'] = dedup(c1['friends'])
c2['friends'] = dedup(c2['friends'])

dbhelper.user_info_db.set(f1, json.dumps(c1))
dbhelper.user_info_db.set(f2, json.dumps(c2))
