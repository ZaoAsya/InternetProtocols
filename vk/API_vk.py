import requests
import argparse
import json
import sys


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("person", type=str, help="ID пользователя", default="104719836")
    parser.add_argument("info", type=str, help="Необходимая информация", default="friends")
    return parser.parse_args()


def get_vk_info(request: str):
    if request == "friends":
        get_friends()
    elif request == "groups":
        get_groups_names()
    elif request == "photos":
        get_photo_albums_names()
    else:
        print('Maybe you want to see anything else?')


def get_person_info(id):
    return make_request('users.get', '5.62', {'user_id': id, 'fields': 'online'})


def make_request(method, v, params):

    def params_to_string(params):
        res = ''
        for k in params:
            res += k + '=' + params[k] + '&'
        return res

    url = "https://api.vk.com/method/{0}?{1}v={2}".format(method, params_to_string(params), v)
    response = requests.get(url).text
    res = json.loads(response)
    return {} if 'error' in res else res['response']


def title(info: str):
    person = get_person_info(PERSON)[0]
    print("\n{0} of {1} {2}\n".format(info, person['first_name'], person['last_name']))


def get_friends():

    def get_online(on):
        return 'no' if on == 0 else 'yes'

    def get_sex(sex):
        return 'Female' if sex == 1 else 'Male'

    data = make_request('friends.get', '5.62', {'user_id': PERSON, 'fields': 'online,sex'})
    title("Friends")
    for d in data['items']:
        print("\nFirst name: {0}\nLast name: {1}\n{2}\nOnline: {3}"
              .format(d['first_name'], d['last_name'], get_sex(d['sex']), get_online(d['online'])))


def get_photo_albums_names():
    data = make_request('photos.getAlbums', '5.74', {'owner_id': PERSON})
    if data['count'] == 0:
        print("No public photo albums've found")
        sys.exit(0)
    title("Photo Albums")
    for d in data['items']:
        print("\nAlbum name: {0}\nSize: {1} photos".format(d['title'], d['size']))


def get_groups_names():
    data = make_request('groups.get', '5.53', {'user_id': PERSON, 'extended': '1'})
    if data == {}:
        print('Sorry.. You need special privileges')
        sys.exit(0)
    title("Groups")
    for d in data['items']:
        print("\nGroup name: {0}\nType: {1}".format(d['name'], d['type']))


def main():
    try:
        global PERSON
        args = get_args()
        PERSON = args.person
        request = args.info
        get_vk_info(request)
    except Exception as ex:
        print(ex)
        sys.exit(0)


if __name__ == "__main__":
    main()
