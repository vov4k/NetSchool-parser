from MySQL import MySQL
import datetime


print("connecting")
mysql = MySQL("config.json")
print("sending query")
res = mysql.fetch("SELECT id, name, last_visit, class, username FROM `users`")
print('got result')
now = datetime.datetime.now()
counter_day = 0
counter_week = 0
for user in res:
    if user['last_visit'] == None:
          
          print('Error!', user['username'])
          print('Additional data', user)
          continue
    if (now - user['last_visit']) < datetime.timedelta(days=1):
          counter_day += 1
    if (now - user['last_visit']) < datetime.timedelta(days=7):
          counter_week += 1
          
print('Last 24 hours active users:', counter_day, 'from', len(res))
    
print('Last week active users:', counter_week, 'from', len(res))
