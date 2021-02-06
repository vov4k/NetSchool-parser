from requests import post as req_post
from json import load as json_load

from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)


with open("config.json", 'r', encoding="utf-8") as file:
    file_upload_key = json_load(file, encoding="utf-8")["file_upload_key"]

with open("README.md", "rb") as file:
    r = req_post("https://netschool.loc/src/upload_file.php", data={'file_upload_key': file_upload_key, 'path': 'doc'}, files={'file': file}, verify=False)
    print(r.text)
