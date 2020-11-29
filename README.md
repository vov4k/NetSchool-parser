Чтобы настроить логин/пароль NetSchool:

Создайте файл `/netschool_pwd.txt` со следующим содержанием:
```
{username}
{password}
```

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

### Requirements

Python modules:
- requests
- bs4
- lxml
- PyMySQL

`py -3 -m pip install -U requests bs4 lxml PyMySQL`