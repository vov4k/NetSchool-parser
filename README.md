## Installation

#### Requirements

Python modules:
- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [lxml](https://pypi.org/project/lxml/)
- [PyMySQL](https://pypi.org/project/PyMySQL/) *with RSA*

or just run `py -3 -m pip install -U requests beautifulsoup4 lxml PyMySQL[rsa]`

#### NetSchool

Создайте файл `/netschool_pwd.txt` со следующим содержанием:
```
{username}
{password}
```

#### MySQL

Чтобы настроить MySQL:
Создайте файл `/MySQL/config.json` со следующим содержанием:
```
{
	"host": "{host}",
	"user": "{username}",
	"password": "{password}",
	"database": "{database}"
}
```
Или скопируйте из секретных источников...
