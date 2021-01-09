#### Requirements

Run `py -3 -m pip install -U -r requirements.txt` in command promt.

Python modules:
- [requests](https://pypi.org/project/requests)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4)
- [lxml](https://pypi.org/project/lxml)
- [PyMySQL](https://pypi.org/project/PyMySQL) *with RSA*

`py -3 -m pip install -U requests beautifulsoup4 lxml PyMySQL[rsa]`

#### Config

Чтобы настроить NetSchool и MySQL:
Создайте файл `/config.json` со следующим содержанием:
```
{
	"db_hostname": "{host}",
	"db_username": "{username}",
	"db_password": "{password}",
	"db_name": "{database}",

	"file_upload_key": "{file_upload_key}",
	
	"netschool_username": "{netschool_username}",
	"netschool_password": "{netschool_password}"
}
```
