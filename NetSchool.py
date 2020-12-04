from os.path import split as os_split, normpath as os_normpath, join as os_join
from requests import Session, post as req_post
from re import search as re_search
from json import load as json_load
from datetime import timedelta
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
import datetime

from traceback import format_exc  # for debugging

from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

from regex import REGEX


def mkpath(*paths):
    return os_normpath(os_join(*paths))


def upload_file(path):
    with open("config.json", 'r', encoding="utf-8") as file:
        file_upload_key = json_load(file, encoding="utf-8")["file_upload_key"]

    with open(path, 'rb') as file:
        r = req_post(
            "https://netschool.npanuhin.me/src/upload_file.php",
            data={'file_upload_key': file_upload_key, 'path': 'doc'},
            files={'file': file}, verify=False
        )

    if r.status_code == 200 and r.text == 'success':
        return "https://netschool.npanuhin.me/doc/" + os_split(path)[1].strip()
    return None


class NetSchoolUser:
    def __init__(self, username, password, download_path):

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
            "UN": username
        }

        self.username = username
        self.password = password
        self.download_path = download_path
        self.sleep_time = 0

        self.at, self.ver = "", ""

        self.session = Session()

    def login(self):
        # netschool.school.ioffe.ru

        r = self.session.get('http://netschool.school.ioffe.ru').text
        soup = BeautifulSoup(r, 'lxml').find('div', class_='info')

        self.login_params['VER'] = soup.find('input', {'name': 'VER'}).get('value').strip()
        self.login_params['LoginType'] = soup.find('input', {'name': 'LoginType'}).get('value').strip()
        self.login_params['LT'] = soup.find('input', {'name': 'LT'}).get('value').strip()

        salt = re_search(REGEX['salt'], r).group(1)

        # salt = r[r.find('salt') + 4: r.find('salt') + 20]
        # salt = salt[salt.find('\'') + 1: salt.rfind('\'')].strip()

        self.login_params['PW2'] = md5((str(salt) + md5(self.password.encode()).hexdigest()).encode()).hexdigest()
        self.login_params['PW'] = self.login_params['PW2'][:len(self.password)]

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

    def download_attachment(self, url, attachment_id):
        params = {
            'AT': self.at,
            'VER': self.ver,
            'attachmentId': attachment_id
        }
        r = self.session.post(url, data=params)

        if r.status_code == 200:
            filepath = mkpath(self.download_path, str(attachment_id) + '.' + os_split(url)[1])
            with open(filepath, 'wb') as file:
                file.write(r.content)
            return filepath

        return None

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
        for announcement in announcements:
            author = announcement.find('div', class_='adver-profile').find('span').text.strip()

            announcement = announcement.find('div', class_='adver-body')

            title = announcement.find('h3')
            title.span.decompose()

            date = datetime.datetime.strptime(announcement.find('div', class_='adver-info').find('span').text.strip(), '%d.%m.%y').date()

            content = announcement.find('div', class_='adver-content')

            for br in content.find_all('br'):
                br.replace_with('\n')

            for fieldset in content.find_all('div', class_='fieldset'):
                fieldset_content = fieldset.find('div').find('span')

                if 'AttachmentSpan' in fieldset_content.get('class') and fieldset_content.find('a').has_attr('href'):
                    fieldset_content = re_search(REGEX["attachment"], fieldset_content.find('a').get('href'))
                    try:
                        link, attachment_id = fieldset_content.group(1), fieldset_content.group(2)
                        if link.startswith('/') or link.startswith('\\'):
                            link = 'http://netschool.school.ioffe.ru' + link

                        new_link = upload_file(self.download_attachment(link, attachment_id))

                        if new_link is None:
                            new_link = link

                        fieldset.replace_with(new_link)

                    except Exception as e:
                        print("Exception in file upload:", e)
                        fieldset.replace_with(fieldset_content)

            links = content.find_all('a')
            for link in links:
                if link.has_attr('title'):
                    to_replace = link.get('title') + ': '
                else:
                    to_replace = ''
                if link.has_attr('href'):
                    to_replace += str(re_search(REGEX['link'], str(link.get('href')))[0])
                    # answer_links.append(str(link.get('href')))
                link.replace_with(to_replace)

            answer.append([
                author,
                title.text,
                date,
                content.text.replace('Присоединенные файлы\n', 'Присоединенные файлы:')
                .replace('\r\n', '\n').replace('\r', '').replace('\t', '').replace('\xa0', '').strip()
            ])

        sleep(self.sleep_time)
        return answer

    # def get_file(self, url, attachment_id):
    #     params = {
    #         'AT': self.at,
    #         'VER': self.ver,
    #         'attachmentId': str(attachment_id)
    #     }
    #     headers, params = self.getHeaders(self.last_page, params, self.cookies)
    #     r = req_post(url, data=params, headers=headers)
    #     self.last_page = url
    #     # if 'Set-Cookie' in r.headers:
    #     #     self.cookies.update(getCookies(r.headers['set-Cookie']))
    #     return r.content

    def get_daily_timetable(self, date=None, get_class=False):
        if date is None:
            date = datetime.datetime.today().date()

        school_year = datetime.datetime.today().date().year
        if datetime.datetime.today().date().month < 9:
            school_year -= 1

        params = {
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

        _class = soup.find('input', {'name': 'PCLID_IUP_label'}).get('value').strip()

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
                    event = re_search(REGEX['timetable_event'], tr[1].find('a').get('href'))
                    event_type, event_id = int(event.group(1)), int(event.group(2))

                    name = re_search(REGEX['event_name_strip'], name).group(1)

                    if 'vacation-day' in tr[1].get('class'):
                        answer.append(['vacation', (start_daytime, end_daytime), name, event_type, event_id])

                    else:
                        answer.append(['event', (start_daytime, end_daytime), name, event_type, event_id])

                else:
                    name = re_search(REGEX['event_name_strip'], name).group(1)
                    answer.append(['lesson', (start_daytime, end_daytime), name])
        else:
            answer = None

        sleep(self.sleep_time)
        if get_class:
            return _class, answer
        return answer

    def get_weekly_timetable(self, date=None, get_class=False):
        if date is None:
            date = datetime.datetime.today().date()
        date = date - timedelta(date.weekday())
        params = {
            'AT': self.at,
            'VER': self.ver,
            'DATE': date.strftime('%d.%m.%y')
        }

        r = self.session.post('http://netschool.school.ioffe.ru/asp/Calendar/WeekViewTimeS.asp', data=params)

        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        soup = soup.find('div', class_='content')

        _class = soup.find('input', {'name': 'PCLID_IUP_label'}).get('value').strip()

        answer = []
        for day in soup.find('table').find_all('tr')[1:]:
            lessons = [lesson.replace('\xa0', ' ').strip() for lesson in list(day.find_all('td')[1].descendants)[::2]]
            answer.append([lesson if lesson != '-' else None for lesson in lessons])

        answer += [None] * (len(answer) - 7)

        sleep(self.sleep_time)
        if get_class:
            return _class, answer
        return answer

    def get_diary(self, date=None, get_class=False):
        if date is None:
            date = datetime.datetime.today().date()
        date = date - timedelta(date.weekday())
        params = {
            'AT': self.at,
            'VER': self.ver,
            'DATE': date.strftime('%d.%m.%y')
        }

        r = self.session.post('http://netschool.school.ioffe.ru/asp/Curriculum/Assignments.asp', data=params)

        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        soup = soup.find('div', class_='content')

        _class = soup.find('input', {'name': 'PCLID_IUP_label'}).get('value').strip()

        answer = {date + timedelta(days=i): [] for i in range(7)}

        def parse_lesson(lesson):
            lesson = lesson.find_all('td')
            start_index = 0 if len(lesson) == 5 else 1

            link_info = re_search(REGEX['lesson_link'], lesson[start_index + 2].find('a').get('href'))

            params = {
                'AT': self.at,
                # 'VER': self.ver,
                'AID': int(link_info.group(1)),
                'CID': int(link_info.group(2)),
                'TP': int(link_info.group(3))
            }

            r = self.session.post('http://netschool.school.ioffe.ru/asp/ajax/Assignments/GetAssignmentInfo.asp', data=params).json()

            if 'isError' in r and r['isError']:
                info = None
            else:
                title = r['data']['strTitle'] if 'strTitle' in r['data'] else ""
                table = r['data']['strTable'] if 'strTable' in r['data'] else ""
                if table:
                    trs = BeautifulSoup(table, 'lxml').find('table').find_all('tr')
                    table = {}
                    for tr in trs:
                        if tr.find('td').find('span', class_='AttachmentSpan') is not None:
                            link_info = re_search(REGEX['attachment'], tr.find('td').find('a').get('href'))

                            link, attachment_id = link_info.group(1), int(link_info.group(2))

                            if link.startswith('/') or link.startswith('\\'):
                                link = 'http://netschool.school.ioffe.ru' + link

                            table[tr.find('th').text.strip()] = upload_file(self.download_attachment(link, attachment_id))
                        else:
                            table[tr.find('th').text.strip()] = tr.find('td').text.strip()

                info = [title, table]

            mark = lesson[start_index + 4].text.strip()
            try:
                mark = int(mark)
            except ValueError:
                pass

            result = [
                lesson[start_index].text.strip(),
                lesson[start_index + 1].text.strip(),
                lesson[start_index + 2].find('a').text.strip(),
                int(lesson[start_index + 3].text),
                mark,
                info
            ]

            return result

        tr_index = 0
        soup = soup.find('table').find_all('tr')[1:]
        while tr_index < len(soup):
            while tr_index < len(soup) and len(soup[tr_index].find_all('td')) < 6:
                tr_index += 1

            cur_day, cur_month, cur_year = soup[tr_index].find_all('td')[0].find('a').text.split(',')[0].strip().split('.')
            cur_date = datetime.date(year=datetime.datetime.strptime(cur_year, '%y').year, month=int(cur_month), day=int(cur_day))

            if cur_date < date or cur_date >= date + timedelta(days=7):
                tr_index += 1
                while tr_index < len(soup) and len(soup[tr_index].find_all('td')) < 6:
                    tr_index += 1
                continue

            answer[cur_date].append(parse_lesson(soup[tr_index]))

            tr_index += 1
            while tr_index < len(soup) and len(soup[tr_index].find_all('td')) < 6:
                if len(soup[tr_index].find_all('td')) == 5:
                    answer[cur_date].append(parse_lesson(soup[tr_index]))

                tr_index += 1

        sleep(self.sleep_time)
        if get_class:
            return _class, answer
        return answer

    # def get_activities(self, date=None):
    #     if date is None:
    #         date = datetime.datetime.today().date()
    #     date = (date - timedelta(date.weekday())).strftime('%d.%m.%y')
    #     params = {
    #         'AT': self.at,
    #         'VER': self.ver,
    #         "PCLID_IUP": "137_0",
    #         'DATE': date
    #     }

    #     r = self.session.post('http://netschool.school.ioffe.ru/asp/Calendar/WeekViewClassesS.asp', data=params)

    #     r = self.handle_security_warning(r)

    #     soup = BeautifulSoup(r.text, 'lxml')
    #     self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
    #     self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

    #     print(soup.find('div', class_='content').find('table').find_all('tr')[1:])

    # def getEvent(self, event_id, event_type):
    #     event_type = {
    #         'event': 1,
    #         '???': 2,  # TODO
    #         '???': 3,  # TODO
    #         'vacation': 4
    #     }[event_type]
    #     params = {
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

    #     r = req_post('http://netschool.school.ioffe.ru/asp/SetupSchool/Calendar/EditEvent.asp', data=params, headers=headers)
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

    nts = NetSchoolUser(user_login, user_password, 'doctmp')

    if not nts.login():
        exit("Login failed")
    print("Login success")

    try:
        pass
        # print("get_announcements():")
        # print(nts.get_announcements())
        # print("get_daily_timetable():")
        # print(nts.get_daily_timetable(get_class=True))
        # print(nts.get_daily_timetable(datetime.date(year=2021, month=1, day=1), get_class=True))
        # print(nts.get_daily_timetable(datetime.date(year=2020, month=11, day=25), get_class=True))
        # print(nts.get_daily_timetable(datetime.date(year=2020, month=6, day=1), get_class=True))  # holidays
        # print("get_weekly_timetable():")
        # print(nts.get_weekly_timetable(get_class=True))
        # print(nts.get_weekly_timetable(datetime.date(year=2020, month=11, day=9), get_class=True))
        # print("get_diary():")
        # print(nts.get_diary(get_class=True))
        # print("get_activities():")
        # print(nts.get_activities())
    except Exception:
        print(format_exc())

    nts.logout()
    print("Logout")


if __name__ == "__main__":
    with open("config.json", 'r', encoding="utf-8") as file:
        config = json_load(file, encoding="utf-8")
        netschool_username, netschool_password = config["netschool_username"], config['netschool_password']

    print("Using login: {} and password: {}".format(netschool_username, netschool_password))
    main(netschool_username, netschool_password)
