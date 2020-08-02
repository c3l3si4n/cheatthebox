import requests
import config
import json
from bs4 import BeautifulSoup
import datetime

USERAGENT = config.USERAGENT
USERNAME = config.USERNAME
PASSWORD = config.PASSWORD
FILENAME = config.OUTPUT_FILENAME
s = requests.Session()
s.headers.update({'User-Agent': USERAGENT})


def log(data):
    print("[*] " + str(data))


def login(username, password):
    html_text = s.get('https://www.hackthebox.eu/login').text
    soup = BeautifulSoup(html_text, 'html.parser')

    ssrf_token = ''
    for input_attr in soup.find_all('input'):
        if input_attr.attrs['name'] == '_token':
            ssrf_token = input_attr.attrs['value']

    log("SSRF Token: " + ssrf_token)
    data = {"_token": ssrf_token, 'email': username, 'password': password}
    s.post('https://www.hackthebox.eu/login', data=data)
    log("Logged in with %s." % username)


def get_point_history(id):
    url = 'https://www.hackthebox.eu/home/users/points/%s' % str(id)
    html_text = s.get(url).text
    soup = BeautifulSoup(html_text, 'html.parser')
    ps = soup.find_all('p')

    solves_list = []

    for p in ps:
        if p.find('span'):
            time = p.text.split('] ')[0][1:]
            name = p.text.split('] ')[1].split(": ")
            name.pop()
            name = ': '.join(name)
            points = int(p.find('code').text)

            time = datetime.datetime.strptime(time, '%d %b %Y %H:%M:%S')
            time = time.isoformat()
            time = str(time)

            solve_name = {"date": time, "name": name, "points": points}
            solves_list.append(solve_name)
    return solves_list


def dump_hof():
    html_text = s.get('https://www.hackthebox.eu/home/hof').text
    soup = BeautifulSoup(html_text, 'html.parser')
    user_list = []
    for tr in soup.find_all("tr"):
        td_list = tr.find_all('td')

        if len(td_list) == 11:
            td1 = td_list[1]
            a_tag = td1.find('a')

            points = td_list[4].text.strip()

            username = a_tag.text

            user_id = a_tag.attrs['href'].split('/profile/')[1]
            log('Saved profile data for username %s' % username)
            solves = get_point_history(user_id)
            log('Saved challenges and machines solves for username %s' % username)

            user_obj = {"id": user_id, "username": username,
                        "points": points, "solves": solves}
            user_list.append(user_obj)
    return user_list


login(USERNAME, PASSWORD)
users = dump_hof()

with open(FILENAME, 'wb') as f:
    data_to_write = json.dumps({"users": users})
    f.write(data_to_write.encode('utf-8'))
# point_history = get_point_history(52045)
