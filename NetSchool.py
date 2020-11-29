import requests
from time import sleep
from bs4 import BeautifulSoup
from datetime import timedelta
import datetime
import re
# from urllib.parse import urlparse

from hashlib import md5

from traceback import format_exc  # for debugging

from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)


def contentLength(params):
    return 2 * len(params) - 1 + sum([len(key) + len(value) for key, value in params.items()])


def getCookies(cookies):
    answer = {}
    while cookies:
        key_i = cookies.find('=')
        key = cookies[:key_i]
        value = cookies[key_i + 1: cookies.find(';')]
        answer[key] = value
        cookies = cookies[cookies.find('path'):]
        cookie_end_i = cookies.find(',') + 1
        if not cookie_end_i:
            break
        while cookie_end_i < len(cookies) and cookies[cookie_end_i] == ' ':
            cookie_end_i += 1
        cookies = cookies[cookie_end_i:]
    return answer


def cookiesToStr(cookies):
    return ';'.join([key + '=' + value for key, value in cookies.items()])


class NetschoolUser:
    def __init__(self, login, password):

        self.login_params = {
            "ECardID": "",
            "CID": "2",
            "PID": "-1",
            "CN": "1",
            "SFT": "2",
            "SCID": "1",
            "optional": "optional",
            "PCLID_IUP": "116_0",
            "ThmID": "1",
            # "PCLID": "116",
            "RPTID": "0",
            "SID": "2589",
            "UN": login
        }
        self.main_headers = {
            # "Host": "netschool.school.ioffe.ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0",
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            # "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            # "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            # "Upgrade-Insecure-Requests": "1",
            # "Pragma": "no-cache",
            # "Cache-Control": "no-cache"
        }

        self.user_login = login
        self.user_password = password
        self.sleep_time = 1

        self.session = requests.Session()
        self.session.headers = self.main_headers

    # def get_menuitem_tabitem(referer, to):
    #   referer = referer[referer.find('asp') + 4:]
    #   table1 = {
    #       'Announce/ViewAnnouncements.asp' : '0',
    #       'Curriculum/Assignments.asp':'16',
    #       'Reports/Reports.asp':'14',
    #       'Calendar/WeekViewTimeS.asp':'12',
    #       'SetupSchool/Calendar/YearView.asp':'12',
    #       'Calendar/DayViewS.asp': '12',
    #       'Calendar/MonthViewS.asp': '12'
    #   }
    #   try:
    #       menuitem = table1[referer]
    #   except Exception:
    #       menuitem = ''
    #   return menuitem, tabitem

    def login(self):
        # netschool.school.ioffe.ru

        r = self.session.get('http://netschool.school.ioffe.ru').text
        soup = BeautifulSoup(r, 'lxml').find('div', class_='info')

        self.login_params['VER'] = soup.find('input', {'name': 'VER'}).get('value').strip()
        self.login_params['LoginType'] = soup.find('input', {'name': 'LoginType'}).get('value').strip()
        self.login_params['LT'] = soup.find('input', {'name': 'LT'}).get('value').strip()

        salt = r[r.find('salt') + 4: r.find('salt') + 20]
        salt = salt[salt.find('\'') + 1: salt.rfind('\'')].strip()

        self.login_params['PW2'] = md5((str(salt) + md5(self.user_password.encode()).hexdigest()).encode()).hexdigest()

        self.login_params['PW'] = self.login_params['PW2'][:len(self.user_password)]

        sleep(self.sleep_time)

        # postlogin
        r = self.session.post('http://netschool.school.ioffe.ru/asp/postlogin.asp', data=self.login_params)

        if r.url.startswith('http://netschool.school.ioffe.ru/asp/error.asp'):
            return False

        soup = BeautifulSoup(r.text, 'lxml')

        if soup.find('form', {'action': '/asp/SecurityWarning.asp'}) is not None:
            params = {
                'ATLIST': soup.find('input', {'name': 'ATLIST'}).get('value').strip().replace('\x01', '%01'),
                'AT': soup.find('input', {'name': 'AT'}).get('value').strip(),
                'VER': soup.find('input', {'name': 'VER'}).get('value').strip(),
                'WarnType': 1
            }

            sleep(self.sleep_time)

            # SecurityWarning
            r = self.session.post('http://netschool.school.ioffe.ru/asp/SecurityWarning.asp', data=params)

            soup = BeautifulSoup(r.text, 'lxml')

        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        sleep(self.sleep_time)

        return True

    def logout(self):
        self.session.post('http://netschool.school.ioffe.ru/asp/logout.asp', data={'AT': self.at, 'VER': self.ver})
        sleep(self.sleep_time)
        del self

    def handleSecurityWarning(self, r):
        soup = BeautifulSoup(r.text, 'lxml').find('form', {'action': '/asp/SecurityWarning.asp'})

        if soup is not None:
            self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
            self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

            params = {
                'WarnType': soup.find('input', {'name': 'ATLIST'}).get('value').strip(),
                'ATLIST': soup.find('input', {'name': 'WarnType'}).get('value').strip(),
                'AT': self.at,
                'VER': self.ver
            }

            sleep(self.sleep_time)

            r = self.session.post('http://netschool.school.ioffe.ru/asp/SecurityWarning.asp', data=params)

            soup = BeautifulSoup(r.text, 'lxml')
            self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
            self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

            params = {
                'LoginType': soup.find('input', {'name': 'LoginType'}).get('value').strip(),
                'AT': self.at,
                'VER': self.ver,
                'TabItem': soup.find('input', {'name': 'TabItem'}).get('value').strip(),
                'MenuItem': soup.find('input', {'name': 'MenuItem'}).get('value').strip()
            }

            sleep(self.sleep_time)

            r = self.session.post(self.last_page, data=params)
        return r

    def getAnnouncements(self):
        params = {'AT': self.at, 'VER': self.ver}
        headers, params = self.getHeaders(self.last_page, params, self.cookies)

        r = requests.post('http://netschool.school.ioffe.ru/asp/Announce/ViewAnnouncements.asp', data=params, headers=headers)
        self.last_page = 'http://netschool.school.ioffe.ru/asp/Announce/ViewAnnouncements.asp'

        r = self.handleSecurityWarning(r)

        if 'Set-Cookie' in r.headers:
            self.cookies.update(getCookies(r.headers['set-Cookie']))

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()
        # parser
        advertisements = soup.find('div', class_='content').find_all('div', class_='advertisement')
        answer = []
        answer_links = []
        for advertisement in advertisements:
            author = advertisement.find('div', class_='adver-profile').find('span').text.strip()
            advertisement = advertisement.find('div', class_='adver-body')
            title = advertisement.find('h3')
            title.span.decompose()
            date = advertisement.find('div', class_='adver-info').find('span').text.strip()
            content = advertisement.find('div', class_='adver-content')
            brs = content.find_all('br')
            for br in brs:
                br.replaceWith('\n')
            fieldsets = content.find_all('div', class_='fieldset')
            for fieldset in fieldsets:
                fieldset_con = fieldset.find('div').find('span')
                if 'AttachmentSpan' in fieldset_con.get('class'):
                    fieldset_con = fieldset_con.find('a')
                    if fieldset_con.has_attr('href'):
                        fieldset_con = fieldset_con.get('href')
                        try:
                            fieldset_con = fieldset_con[fieldset_con.find('(') + 1:fieldset_con.rfind(')')]
                            fieldset_id = fieldset_con[fieldset_con.rfind(',') + 1:].strip()
                            fieldset_con = fieldset_con[fieldset_con.find('\'') + 1:fieldset_con.rfind('\'')].strip()
                            if fieldset_con.startswith('/') or fieldset_con. startswith('\\'):
                                fieldset_con = 'http://netschool.school.ioffe.ru' + fieldset_con
                            answer_links.append([fieldset_con, fieldset_id])
                            fieldset.replaceWith(fieldset_con)
                        except Exception:
                            pass
            links = content.find_all('a')
            for link in links:
                if link.has_attr('title'):
                    to_replace = link.get('title') + ': '
                else:
                    to_replace = ''
                if link.has_attr('href'):
                    to_replace += str(re.search(r'((https?:\/\/)|\/)[^\s]*', str(link.get('href')))[0])
                    answer_links.append(str(link.get('href')))
                link.replaceWith(to_replace)
            content = content.text.replace('Присоединенные файлы\n', 'Присоединенные файлы:').strip()
            answer.append([author, title.text, date, content])

        # for link in range(len(answer_links)):
        #     if type(answer_links[link]) == list and urlparse(answer_links[link][0]).netloc == 'netschool.school.ioffe.ru':
        #         file_name = urlparse(answer_links[link][0]).path
        #         file_name = file_name[file_name.rfind('/') + 1:]
        #         with open('modules/tmp/' + file_name, 'wb') as file:
        #             file.write(self.getFile(answer_links[link][0], answer_links[link][1]))
        #         answer_links[link] = [1, file_name, answer_links[link][0]]
        #     else:
        #         answer_links[link] = [0, answer_links[link]]
        sleep(self.sleep_time)

        return answer

    def getFile(self, url, attachment_id):
        params = {
            'AT': self.at,
            'VER': self.ver,
            'attachmentId': str(attachment_id)
        }
        headers, params = self.getHeaders(self.last_page, params, self.cookies)
        r = requests.post(url, data=params, headers=headers)
        self.last_page = url
        if 'Set-Cookie' in r.headers:
            self.cookies.update(getCookies(r.headers['set-Cookie']))
        return r.content

    def getDailyTimetable(self, date=None):
        if date is None:
            date = datetime.datetime.today().date()
        date = date.strftime('%d.%m.%y')
        params = {
            'LoginType': '0',
            'AT': self.at,
            'VER': self.ver,
            # 'MenuItem': '0',
            # 'TabItem': '30',
            'DATE': date
        }
        headers, params = self.getHeaders(self.last_page, params, self.cookies)

        r = requests.post('http://netschool.school.ioffe.ru/asp/Calendar/DayViewS.asp', data=params, headers=headers)
        self.last_page = 'http://netschool.school.ioffe.ru/asp/Calendar/DayViewS.asp'

        r = self.handleSecurityWarning(r)
        if 'Set-Cookie' in r.headers:
            self.cookies.update(getCookies(r.headers['set-Cookie']))
        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()
        # parser
        answer = []
        soup = soup.find('div', class_='content')
        if soup.find('div', 'alert-info') is None:
            trs = soup.find('table').find_all('tr')[1:]
            for tr in trs:
                tr = tr.find_all('td')
                time = tr[0].text.strip().replace('\xa0', ' ')
                name = tr[1].text.strip().replace('\xa0', ' ')

                if tr[1].get('class'):
                    try:
                        event_id = tr[1].find('a').get('href')
                        event_id = event_id[:event_id.rfind(')')]
                        event_id = int(event_id[event_id.rfind(',') + 1:])
                    except Exception:
                        event_id = None
                if tr[1].get('class') is not None and 'vacation-day' in tr[1].get('class'):
                    answer.append([time, name, 'vacation', event_id])
                elif tr[1].get('class') is not None and 'school-event' in tr[1].get('class'):
                    answer.append([time, name, 'event', event_id])
                else:
                    if name.startswith('Урок:'):
                        name = name[5:].strip()
                    answer.append([time, name, 'lesson'])
        else:
            answer = soup.find('div', 'alert-info').text.strip()
        sleep(self.sleep_time)
        return answer

    def getWeeklyTimetable(self, date=None):
        if date is None:
            date = datetime.datetime.today().date()
        date = (date - timedelta(date.weekday())).strftime('%d.%m.%y')
        params = {
            'LoginType': '0',
            'AT': self.at,
            'VER': self.ver,
            # 'MenuItem': '0',
            # 'TabItem': '30',
            'Relay': '-1',
            'DATE': date
        }
        headers, params = self.getHeaders(self.last_page, params, self.cookies)

        r = requests.post('http://netschool.school.ioffe.ru/asp/Calendar/WeekViewTimeS.asp', data=params, headers=headers)
        self.last_page = 'http://netschool.school.ioffe.ru/asp/Calendar/WeekViewTimeS.asp'

        r = self.handleSecurityWarning(r)
        if 'Set-Cookie' in r.headers:
            self.cookies.update(getCookies(r.headers['set-Cookie']))
        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()
        # parser
        answer = []
        soup = soup.find('div', class_='content')
        # with open('netschool.html', 'w', encoding='UTF8') as file:
        # file.write(r`.text)
        trs = soup.find('table').find_all('tr')[1:]
        for tr in trs:
            lessons = list(tr.find_all('td')[1].descendants)[::2]
            lessons = list(map(lambda x: x.replace('\xa0', ' ').strip() if x.replace('\xa0', ' ').strip() != '-' else None, lessons))
            answer.append(lessons)

        while len(answer) < 7:
            answer.append([None])
        sleep(self.sleep_time)
        return answer

    # def getEvent(self, event_id, event_type):
    #     event_type = {
    #         'event': 1,
    #         '???': 2,  # TODO
    #         '???': 3,  # TODO
    #         'vacation': 4
    #     }[event_type]
    #     params = {
    #         'LoginType': '0',
    #         'AT': self.at,
    #         'VER': self.ver,
    #         'EventID': str(event_id),
    #         'BackPage': '/asp/Calendar/DayViewS.asp',
    #         'EventType': str(event_type),   # TODO
    #         # 'DATE': date,
    #         # 'MenuItem': '0',
    #         # 'TabItem': '30',
    #     }
    #     headers, params = self.getHeaders(self.last_page, params, self.cookies)

    #     r = requests.post('http://netschool.school.ioffe.ru/asp/SetupSchool/Calendar/EditEvent.asp', data=params, headers=headers)
    #     self.last_page = 'http://netschool.school.ioffe.ru/asp/SetupSchool/Calendar/EditEvent.asp'

    #     r = self.handleSecurityWarning(r)
    #     if 'Set-Cookie' in r.headers:
    #         self.cookies.update(getCookies(r.headers['set-Cookie']))
    #     soup = BeautifulSoup(r.text, 'lxml')
    #     self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
    #     self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()
    #     # parser
    #     answer = {}
    #     soup = soup.find('div', class_='content').find('form')
    #     labels = soup.find_all('div', class_='form-group')
    #     for label in labels:
    #         key = label.find('label').text.strip()
    #         if key:
    #             value = label.find('input').get('value').strip()
    #         if key and value:
    #             answer[key] = value

    #     sleep(self.sleep_time)
    #     return answer


def main(user_login, user_password):  # For development
    print("Starting...")

    nts = NetschoolUser(user_login, user_password)
    if not nts.login():
        exit("Login failed")
    print('Login success')

    try:
        pass
        # print('getAnnouncements():')
        # print(nts.getAnnouncements())
        # print('getDailyTimetable:')
        # print(nts.getDailyTimetable())
        # print(nts.getDailyTimetable(datetime.date(year=2019, month=6, day=3)))  # nothing
        # print(nts.getDailyTimetable(datetime.date(year=2019, month=5, day=1)))  # holidays
        # print('getWeeklyTimetable():')
        # print(nts.getWeeklyTimetable())
    except Exception:
        print(format_exc())

    nts.logout()
    print('Logout success')


if __name__ == "__main__":
    with open("netschool_pwd.txt", 'r', encoding="utf-8") as file:
        netschool_login, netschool_pwd = map(str.strip, file.readlines())

    print("Using login: {} and password: {}".format(netschool_login, netschool_pwd))

    main(netschool_login, netschool_pwd)
