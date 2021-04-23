from MySQL import MySQL
import datetime


print("Connecting...")
mysql = MySQL("config.json")

print("Sending query...")
res = mysql.fetch("SELECT `id`, `name`, `last_visit`, `class`, `username` FROM `users`")
print("Got result")

now = datetime.datetime.now()
counter_day = 0
counter_week = 0
counter_class = {}
for user in res:
    if user["last_visit"] is None:
        print("Error!", user["username"])
        print("Additional data", user)
        continue

    if (now - user["last_visit"]) < datetime.timedelta(days=1):
        counter_day += 1

    if (now - user["last_visit"]) < datetime.timedelta(days=7):
        counter_week += 1

    class_ = user["class"]

    if class_ not in counter_class:
        counter_class[class_] = 0

    counter_class[class_] += 1

print("Last 24 hours active users: {}/{}".format(counter_day, len(res)))

print("Last week active users: {}/{}".format(counter_week, len(res)))

print("Class stats:\n{}".format(
    "  |  ".join("{}: {}".format(class_, cnt) for class_, cnt in sorted(counter_class.items(), key=lambda x: -x[1]))
))
