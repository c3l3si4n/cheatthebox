import requests
import config
import json
from bs4 import BeautifulSoup
import datetime
import dateutil.parser

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


def calculate_cheater_probability(solves, threshold):
    solves_map = {}
    for solve in solves:
        time = dateutil.parser.parse(solve['date'])
        formatted_day = time.strftime("%d/%m/%y")
        if formatted_day not in solves_map:
            solves_map.update({formatted_day: {"day": formatted_day}})
        if 'points' not in solves_map[formatted_day]:
            solves_map[formatted_day]['points'] = 0
        if 'number_of_solves' not in solves_map[formatted_day]:
            solves_map[formatted_day]['number_of_solves'] = 0
        if 'solves' not in solves_map[formatted_day]:
            solves_map[formatted_day]['solves'] = []
        solves_map[formatted_day]['number_of_solves'] += 1

        solves_map[formatted_day]['points'] = solves_map[formatted_day]['points'] + solve['points']
        solve['time'] = time.strftime("%H:%M:%S")
        del solve['date']
        solves_map[formatted_day]['solves'].append(solve)

    solves_map_cleaned = []
    final_obj = {}
    points_sum = 0
    counter = 0
    for key in solves_map:
        solves_map[key]['solves'] = sorted(
            solves_map[key]['solves'], key=lambda k: k['time'])
        if not solves_map[key]['points'] < threshold:
            points_sum += solves_map[key]['points']
            counter += 1
            solves_map_cleaned.append(solves_map[key])
    if len(solves_map_cleaned) > 0:
        avg_points = int(points_sum / counter)

        final_obj = {"suspicious": True,
                     "avg_points": avg_points, "cases": solves_map_cleaned}
    else:
        final_obj = {"suspicious": False, "cases": []}

    return final_obj


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
            log('Analysing if %s is a cheater.' % username)
            analysis = calculate_cheater_probability(solves, 400)

            user_obj = {"id": user_id, "username": username,
                        "points": points, "analysis": analysis, "solves": solves}
            user_list.append(user_obj)

    return user_list


# login(USERNAME, PASSWORD)
# users = dump_hof()


def dump_users_to_file():
    with open(FILENAME, 'wb') as f:
        data_to_write = json.dumps({"users": users})
        f.write(data_to_write.encode('utf-8'))


dump_users_to_file()
