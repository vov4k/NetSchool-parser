import datetime
# from src.password_hash import hexMD5 as cusom_md5
from hashlib import md5
from json import load as json_load
from os.path import split as os_split, normpath as os_normpath, join as os_join, isdir as os_isdir, exists as os_exists
from re import search as re_search
from shutil import copyfile
from time import sleep
from traceback import format_exc  # for debugging

import mysql.connector
import telegram
from bs4 import BeautifulSoup
from requests import Session, post as req_post
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)

from regex import REGEX


def mkpath(*paths):
    return os_normpath(os_join(*paths))


def md5_hash(text):
    # return cusom_md5(text)
    return md5(text.encode('cp1251')).hexdigest()


def upload_attachment(path, file_upload_key):
    if os_isdir("/var/www/netschool/www/doc"):
        try:
            copyfile(path, mkpath("/var/www/netschool/www/doc/", os_split(path)[1].strip()))
            return "/src/get_doc.php?file=" + os_split(path)[1].strip()
        except Exception:
            return None

    print("Uploading file...")

    with open(path, "rb") as file:
        r = req_post(
            "https://netschool.npanuhin.me/src/upload_file.php",
            data={'file_upload_key': file_upload_key, 'path': 'doc'},
            files={'file': file}, verify=False
        )

    if r.status_code == 200 and r.text == 'success':
        return "/src/get_doc.php?file=" + os_split(path)[1].strip()
    return None


Attachments = {}


class NetSchoolUser:
    def __init__(self, username, password, download_path, config_path):

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

        self.name = None
        self.class_ = None
        self.mail = None

        with open(config_path, 'r', encoding="utf-8") as file:
            self.file_upload_key = json_load(file)["file_upload_key"]

        self.at, self.ver = "", ""

        self.empty_soup = BeautifulSoup('', 'lxml')
        self.session = Session()

    def __del__(self):
        self.logout()

    def get_name(self, soup):
        self.name = soup.find('div', class_='header').find('a',
                                                           {'href': 'JavaScript:openPersonalSettings()'}).text.strip()

    def get_class(self, soup):
        self.class_ = soup.find('div', class_='content').find('input', {'name': 'PCLID_IUP_label'}).get('value').strip()

    def get_mail(self, soup):
        mail = soup.find('ul', class_='top-right-menu').find('span', class_='mail').find('span', class_='numberMail')
        self.mail = None if mail is None else mail.text.strip()

    def login(self):
        r = self.session.get('http://netschool.school.ioffe.ru').text
        soup = BeautifulSoup(r, 'lxml').find('div', class_='info')

        self.login_params['VER'] = soup.find('input', {'name': 'VER'}).get('value').strip()
        self.login_params['LoginType'] = soup.find('input', {'name': 'LoginType'}).get('value').strip()
        self.login_params['LT'] = soup.find('input', {'name': 'LT'}).get('value').strip()

        salt = re_search(REGEX['salt'], r).group(1).strip()

        self.login_params['PW2'] = md5_hash(str(salt) + md5_hash(self.password))
        self.login_params['PW'] = self.login_params['PW2'][:len(self.password)]

        sleep(self.sleep_time)

        # postlogin
        r = self.session.post('http://netschool.school.ioffe.ru/asp/postlogin.asp', data=self.login_params)

        if r.url.startswith('http://netschool.school.ioffe.ru/asp/error.asp'):
            error_text = re_search(REGEX['error_message'], r.text).group(2).strip()
            return False if error_text.lower() == "Неправильный пароль или имя пользователя".lower() else None

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
                'TabItem': soup.find('input', {'name': 'TabItem'}).get('value').strip() if soup.find('input', {
                    'name': 'TabItem'}) is not None else None,
                'MenuItem': soup.find('input', {'name': 'MenuItem'}).get('value').strip() if soup.find('input', {
                    'name': 'MenuItem'}) is not None else None
            }

            sleep(self.sleep_time)

            r = self.session.post(self.last_page, data=params)
        return r

    def download_attachment(self, url, attachment_id):
        path = mkpath(self.download_path, str(attachment_id) + '.' + os_split(url)[1])
        if os_exists(path):
            return path

        print("Downloading file...")

        r = self.session.post(url, data={
            'AT': self.at,
            'VER': self.ver,
            'attachmentId': attachment_id
        })

        if r.status_code == 200:
            with open(path, 'wb') as file:
                file.write(r.content)
            return path

        return None

    def get_announcements(self):
        params = {
            'AT': self.at,
            'VER': self.ver
        }
        r = self.session.post('http://netschool.school.ioffe.ru/asp/Announce/ViewAnnouncements.asp', data=params)
        self.last_page = 'http://netschool.school.ioffe.ru/asp/Announce/ViewAnnouncements.asp'
        r = self.handle_security_warning(r)

        soup = BeautifulSoup(r.text, 'lxml')
        self.at = soup.find('input', {'name': 'AT'}).get('value').strip()
        self.ver = soup.find('input', {'name': 'VER'}).get('value').strip()

        self.get_name(soup)
        self.get_mail(soup)

        announcements = soup.find('div', class_='content').find_all('div', class_='advertisement')
        answer = []
        for announcement in announcements:
            author = announcement.find('div', class_='adver-profile').find('span').text.strip()

            announcement = announcement.find('div', class_='adver-body')

            title = announcement.find('h3')
            title.span.decompose()

            date = datetime.datetime.strptime(announcement.find('div', class_='adver-info').find('span').text.strip(),
                                              '%d.%m.%y').date()

            content = announcement.find('div', class_='adver-content')

            for br in content.find_all('br'):
                br.replace_with('\n')
            attachments_paths = []
            for fieldset in content.find_all('div', class_='fieldset'):
                fieldset_content = fieldset.find('div').find('span')

                if 'AttachmentSpan' in fieldset_content.get('class') and fieldset_content.find('a').has_attr('href'):
                    link_obj = fieldset_content.find('a')

                    link, attachment_id = re_search(REGEX['attachment'], link_obj.get('href')).groups()
                    if link.startswith('/') or link.startswith('\\'):
                        link = 'http://netschool.school.ioffe.ru' + link

                    try:
                        attachment_path = self.download_attachment(link, attachment_id)
                        attachments_paths.append(attachment_path)
                        new_link = upload_attachment(attachment_path,
                                                     self.file_upload_key)
                        assert new_link is not None

                    except Exception as e:
                        print("Exception in file upload:", e)
                        new_link = link

                    new_link_obj = self.empty_soup.new_tag('a', href=new_link, target='_blank')
                    new_link_obj.string = link_obj.text
                    fieldset.replace_with(str(new_link_obj))

            for link_obj in content.find_all('a'):
                if link_obj.has_attr('href'):
                    new_link_obj = self.empty_soup.new_tag('a', href=str(link_obj.get('href')).strip(), target='_blank')
                    new_link_obj.string = link_obj.text
                    link_obj.replace_with(str(new_link_obj))

            answer.append({
                "author": author,
                "title": title.text,
                "date": date,
                "content": content.text.replace('Присоединенные файлы\n', 'Присоединенные файлы:')
                    .replace('\r\n', '\n').replace('\r', '').replace('\t', '').replace('\xa0', '')
                    .replace(' \n', '\n').replace('\n ', '\n')  # .replace('\n\n', '\n')
                    .strip(),
            })
            Attachments[hash(frozenset(answer[-1].items()))] = attachments_paths

        sleep(self.sleep_time)
        return answer


def push_announcements(ns_announcements):
    cursor.execute("SELECT * FROM `announcements`")
    db_announcements = cursor.fetchall()
    TOKEN = "5301269049:AAHvi6epEA39Idjblb6v4DOa5UBvvil3SZA"
    bot = telegram.Bot(token=TOKEN)
    chat_id = -1001783691511
    announcements_withot_id = []
    for announcement in db_announcements:
        withot_id = {
            "author": announcement["author"],
            "title": announcement["title"],
            "date": announcement["date"],
            "content": announcement["content"]
        }
        announcements_withot_id.append(withot_id)
        if withot_id not in ns_announcements:
            if not bot.deleteMessage(chat_id, announcement["id"]):
                bot.editMessageText(chat_id=chat_id, message_id=announcement["id"],
                                    text=f'<del>{prepare_to_msg(announcement)}</del>', parse_mode="HTML")
            cursor.execute('DELETE FROM `announcements` WHERE `id` = %s', (announcement["id"],))
    for announcement in ns_announcements:
        if announcement not in announcements_withot_id:
            text = prepare_to_msg(announcement)
            message_id = bot.send_message(chat_id, text, parse_mode="HTML")["message_id"]
            for attachment in Attachments[hash(frozenset(announcement.items()))]:
                bot.send_document(chat_id=chat_id, document=open(attachment, 'rb'))
            announcement["id"] = message_id
            cursor.execute('INSERT INTO `announcements` VALUES (%(id)s, %(author)s, %(title)s, %(date)s, %(content)s)',
                           announcement)
    print(db_announcements)


def prepare_to_msg(announcement):
    return f'<b>{announcement["title"]}</b>[{announcement["author"]}] {announcement["date"]}\n{announcement["content"]}'


def main(user_login, user_password):  # For development
    print("Starting...")

    nts = NetSchoolUser(user_login, user_password, 'doctmp', 'config.json')

    if not nts.login():
        exit("Login failed")
    print("Login success")

    try:
        print("get_announcements():")
        nts_ann = nts.get_announcements()
        print(nts_ann)
        push_announcements(nts_ann)

        print("Name:", nts.name)
        print("Class:", nts.class_)
        print("Mail:", nts.mail)
    except Exception:
        print(format_exc())

    nts.logout()
    print("Logout")


if __name__ == "__main__":
    with open("config.json", 'r', encoding="utf-8") as file:
        config = json_load(file)
        netschool_username, netschool_password = config["netschool_username"], config['netschool_password']
        cnx = mysql.connector.connect(user=config["db_username"], password=config["db_password"],
                                      host=config["db_hostname"],
                                      database=config["db_name"])
        cursor = cnx.cursor(dictionary=True)

    print("Using login: {} and password: {}".format(netschool_username, netschool_password))
    main(netschool_username, netschool_password)
    cnx.commit()

    cursor.close()
    cnx.close()
