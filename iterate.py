from MySQL import MySQL
import datetime

from json import dumps

from NetSchool import NetSchoolUser

from traceback import format_exc

DOCPATH = 'doctmp'


def every_school_year_day(year=None):
    if year is None:
        year = datetime.datetime.today().year
        if datetime.datetime.today().month < 9:
            year -= 1

    for i in range((datetime.date(year + 1, 6, 1) - datetime.date(year, 9, 1)).days):
        yield datetime.date(year, 9, 1) + datetime.timedelta(days=i)


def infinite():
    while True:
        try:
            onetime()
        except Exception:
            print(format_exc())


def onetime():
    mysql = MySQL("config.json")

    people = mysql.query("SELECT * FROM `users`")

    announcements_sql = [
        "LOCK TABLES announcements WRITE;",
        "TRUNCATE TABLE `announcements`;"
    ]

    got_announcements = False

    for person in people:

        print("Running for person | {} {}...".format(person["first_name"], person["last_name"]))

        nts = NetSchoolUser(person["username"], person["password"], DOCPATH)

        name = None
        status = 0

        try:

            if nts.login():
                print("Login success")
                status = 1

                if not got_announcements:
                    try:
                        announcements = nts.get_announcements()
                        print("Got announcements")
                        for author, title, date, text in announcements:
                            announcements_sql.append(
                                "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES (\"{}\", \"{}\", \"{}\", \"{}\");".format(author, title, date, text)
                            )

                        got_announcements = True
                    except Exception:
                        print(format_exc())

                try:

                    timetable = {}
                    for day in every_school_year_day():
                        print("Getting timetable for day {}...".format(day))
                        try:
                            if name is None:
                                name, cur_timetable = nts.get_daily_timetable(date=day, get_name=True)
                            else:
                                cur_timetable = nts.get_daily_timetable(date=day)

                            if cur_timetable is not None:
                                for item in cur_timetable:
                                    item[1][0] = item[1][0].strftime("%Y-%m-%d %H:%M:%S")
                                    item[1][1] = item[1][1].strftime("%Y-%m-%d %H:%M:%S")

                            timetable[day.strftime("%Y-%m-%d")] = cur_timetable

                        except Exception:
                            print(format_exc())
                            timetable[day.strftime("%Y-%m-%d")] = None

                    mysql.query("UPDATE `users` SET `timetable` = %s WHERE `id` = %s", (dumps(timetable, ensure_ascii=False), person["id"]))

                except Exception:
                    print(format_exc())

            else:
                print("Login failed")

            nts.logout()
            print("Logout\n")

            if name is not None:
                last_name, first_name = map(str.strip, name.split())

            if status == 1:
                mysql.query("UPDATE `users` SET `first_name` = %s, `last_name` = %s, `last_update` = %s WHERE `id` = %s", (
                    first_name, last_name,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    person["id"]
                ))

            else:
                mysql.query("DELETE FROM `users` WHERE `id` = %s", (person["id"],))

        except Exception:
            print(format_exc())

        del nts

        # break

    for request in announcements_sql + ["UNLOCK TABLES;"]:
        mysql.query(request)

    del mysql


if __name__ == "__main__":
    # onetime()
    infinite()
