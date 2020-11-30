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


class NetschoolUser:
    def __init__(self, login, password):

        self.login_params = {
            # "ECardID": "",
            "CID": "2",
            "PID": "-1",
            "CN": "1",
            "SFT": "2",
            "SCID": "1",
            # "optional": "optional",
            "PCLID_IUP": "116_0",
            # "ThmID": "1",
            "PCLID": "116",
            "RPTID": "0",
            "SID": "2589",
            "UN": login
        }

        self.user_login = login
        self.user_password = password
        self.sleep_time = 0.5

        self.at, self.ver = "", ""

        self.session = requests.Session()

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

    def handle_security_warning(self, r):
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

    def get_announcements(self):
        params = {
            'AT': self.at,
            'VER': self.ver
        }
        r = self.session.post('http://netschool.school.ioffe.ru/asp/Announce/ViewAnnouncements.asp', data=params)

        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        announcements = soup.find('div', class_='content').find_all('div', class_='advertisement')
        answer = []
        # answer_links = []
        for advertisement in announcements:
            author = advertisement.find('div', class_='adver-profile').find('span').text.strip()

            advertisement = advertisement.find('div', class_='adver-body')

            title = advertisement.find('h3')
            title.span.decompose()

            date = datetime.datetime.strptime(advertisement.find('div', class_='adver-info').find('span').text.strip(), '%d.%m.%y').date()

            content = advertisement.find('div', class_='adver-content')

            for br in content.find_all('br'):
                br.replace_with('\n')

            for fieldset in content.find_all('div', class_='fieldset'):

                fieldset_content = fieldset.find('div').find('span')

                if 'AttachmentSpan' in fieldset_content.get('class'):
                    fieldset_content = fieldset_content.find('a')
                    if fieldset_content.has_attr('href'):
                        fieldset_content = fieldset_content.get('href')
                        try:
                            fieldset_content = fieldset_content[fieldset_content.find('(') + 1:fieldset_content.rfind(')')]
                            # fieldset_id = fieldset_content[fieldset_content.rfind(',') + 1:].strip()
                            fieldset_content = fieldset_content[fieldset_content.find('\'') + 1:fieldset_content.rfind('\'')].strip()

                            if fieldset_content.startswith('/') or fieldset_content.startswith('\\'):
                                fieldset_content = 'http://netschool.school.ioffe.ru' + fieldset_content
                            # answer_links.append([fieldset_content, fieldset_id])
                            fieldset.replaceWith(fieldset_content)
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
                    # answer_links.append(str(link.get('href')))
                link.replaceWith(to_replace)

            answer.append([
                author,
                title.text,
                date,
                content.text.replace('Присоединенные файлы\n', 'Присоединенные файлы:')
                .replace('\r\n', '\n').replace('\t', '').replace('\xa0', '').strip()
            ])

        # for link in range(len(answer_links)):
        #     if type(answer_links[link]) == list and urlparse(answer_links[link][0]).netloc == 'netschool.school.ioffe.ru':
        #         file_name = urlparse(answer_links[link][0]).path
        #         file_name = file_name[file_name.rfind('/') + 1:]
        #         with open('modules/tmp/' + file_name, 'wb') as file:
        #             file.write(self.get_file(answer_links[link][0], answer_links[link][1]))
        #         answer_links[link] = [1, file_name, answer_links[link][0]]
        #     else:
        #         answer_links[link] = [0, answer_links[link]]

        sleep(self.sleep_time)
        return answer

    def get_file(self, url, attachment_id):
        params = {
            'AT': self.at,
            'VER': self.ver,
            'attachmentId': str(attachment_id)
        }
        headers, params = self.getHeaders(self.last_page, params, self.cookies)
        r = requests.post(url, data=params, headers=headers)
        self.last_page = url
        # if 'Set-Cookie' in r.headers:
        #     self.cookies.update(getCookies(r.headers['set-Cookie']))
        return r.content

    def get_daily_timetable(self, date=None):
        if date is None:
            date = datetime.datetime.today().date()

        if datetime.datetime.today().date().month >= 9:
            school_year = datetime.datetime.today().date().year
        else:
            school_year = datetime.datetime.today().date().year - 1

        params = {
            # 'LoginType': '0',
            'AT': self.at,
            'VER': self.ver,
            'DATE': date.strftime('%d.%m.%y')
        }
        r = self.session.post('http://netschool.school.ioffe.ru/asp/Calendar/DayViewS.asp', data=params)

        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        soup = soup.find('div', class_='content')

        if soup.find('div', 'alert-info') is None:
            answer = []
            for tr in soup.find('table').find_all('tr')[1:]:
                tr = tr.find_all('td')
                start_daytime, end_daytime = map(str.strip, tr[0].text.strip().replace('\xa0', ' ').split('-'))
                name = tr[1].text.strip().replace('\xa0', ' ')

                try:
                    start_daytime = datetime.datetime.combine(date, datetime.datetime.strptime(start_daytime, "%H:%M").time())
                    end_daytime = datetime.datetime.combine(date, datetime.datetime.strptime(end_daytime, "%H:%M").time())
                except ValueError:
                    start_date, start_time = start_daytime.split(' ')
                    end_date, end_time = end_daytime.split(' ')

                    start_day, start_month = map(int, start_date.split('.'))
                    if start_month >= 9:
                        start_date = datetime.date(year=school_year, month=start_month, day=start_day)
                    else:
                        start_date = datetime.date(year=school_year + 1, month=start_month, day=start_day)

                    end_day, end_month = map(int, end_date.split('.'))
                    if end_month >= 9:
                        end_date = datetime.date(year=school_year, month=end_month, day=end_day)
                    else:
                        end_date = datetime.date(year=school_year + 1, month=end_month, day=end_day)

                    start_daytime = datetime.datetime.combine(
                        start_date,
                        datetime.datetime.strptime(start_time, "%H:%M").time()
                    )
                    end_daytime = datetime.datetime.combine(
                        end_date,
                        datetime.datetime.strptime(end_time, "%H:%M").time()
                    )

                if tr[1].get('class') is not None:
                    try:
                        event_id = tr[1].find('a').get('href')
                        event_id = event_id[:event_id.rfind(')')]
                        event_id = int(event_id[event_id.rfind(',') + 1:])
                    except Exception:
                        event_id = None

                    if 'vacation-day' in tr[1].get('class'):
                        answer.append(['vacation', (start_daytime, end_daytime), name, event_id])

                    elif 'school-event' in tr[1].get('class'):
                        answer.append(['event', (start_daytime, end_daytime), name, event_id])

                else:
                    if name.startswith('Урок:'):
                        name = name[5:].strip()
                    answer.append(['lesson', (start_daytime, end_daytime), name])
        else:
            answer = None

        sleep(self.sleep_time)
        return answer

    def get_weekly_timetable(self, date=None):
        if date is None:
            date = datetime.datetime.today().date()
        date = (date - timedelta(date.weekday())).strftime('%d.%m.%y')
        params = {
            # 'LoginType': '0',
            'AT': self.at,
            'VER': self.ver,
            # 'Relay': '-1',
            'DATE': date
        }

        r = self.session.post('http://netschool.school.ioffe.ru/asp/Calendar/WeekViewTimeS.asp', data=params)

        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        answer = []
        for day in soup.find('div', class_='content').find('table').find_all('tr')[1:]:
            lessons = [lesson.replace('\xa0', ' ').strip() for lesson in list(day.find_all('td')[1].descendants)[::2]]
            answer.append([lesson if lesson != '-' else None for lesson in lessons])

        answer += [None] * (len(answer) - 7)

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

    #     r = self.handle_security_warning(r)
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
        print('get_announcements():')
        print(nts.get_announcements())
        # print('get_daily_timetable:')
        # print(nts.get_daily_timetable())
        # print(nts.get_daily_timetable(datetime.date(year=2021, month=1, day=1)))
        # print(nts.get_daily_timetable(datetime.date(year=2020, month=11, day=25)))
        # print(nts.get_daily_timetable(datetime.date(year=2020, month=6, day=1)))  # holidays
        # print('get_weekly_timetable():')
        # print(nts.get_weekly_timetable())
        # print(nts.get_weekly_timetable(datetime.date(year=2020, month=11, day=9)))
    except Exception:
        print(format_exc())

    nts.logout()
    print('Logout')


if __name__ == "__main__":
    with open("netschool_pwd.txt", 'r', encoding="utf-8") as file:
        netschool_login, netschool_pwd = map(str.strip, file.readlines())

    print("Using login: {} and password: {}".format(netschool_login, netschool_pwd))

    main(netschool_login, netschool_pwd)
