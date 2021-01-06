from MySQL import MySQL
import datetime

from json import dumps

from NetSchool import NetSchoolUser

from traceback import format_exc

DOCPATH = 'doctmp'


def day_period(day_start, day_end):
    for i in range((day_end - day_start).days):
        yield day_start + datetime.timedelta(days=i)


def every_school_year_day(year=None):
    if year is None:
        year = datetime.datetime.today().year
        if datetime.datetime.today().month < 9:
            year -= 1

    yield from day_period(
        datetime.date(year, 9, 1),
        datetime.date(year + 1, 6, 1)
    )


def infinite():
    mysql = MySQL("config.json")
    while True:
        try:
            run_person(
                mysql,
                mysql.query("SELECT * FROM `users` ORDER BY `last_update` LIMIT 1")[0]
            )
        except Exception:
            print(format_exc())

    del mysql


def run_person(mysql, person):

    announcements_sql = [
        "LOCK TABLES announcements WRITE;",
        "TRUNCATE TABLE `announcements`;"
    ]

    print("Running for person | {} {}...".format(person["first_name"], person["last_name"]))

    nts = NetSchoolUser(person["username"], person["password"], DOCPATH)

    name = None

    try:

        if nts.login():
            print("Login success")

            # Announcements:
            try:
                announcements = nts.get_announcements()
                print("Got announcements")
                for author, title, date, text in announcements:
                    announcements_sql.append(
                        "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES (\"{}\", \"{}\", \"{}\", \"{}\");".format(author, title, date, text)
                    )

                for request in announcements_sql:
                    mysql.query(request)
                mysql.query("UNLOCK TABLES;")

            except Exception:
                print(format_exc())

            # Timetable:
            timetable = {}
            try:
                if person["last_update"] is None:
                    today = datetime.datetime.today()
                    monday = today - datetime.timedelta(days=today.weekday())
                    cur_period = day_period(monday, monday + datetime.timedelta(days=7))

                else:
                    cur_period = every_school_year_day()

                for day in cur_period:
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

            # General info (first name, last name, last update):
            if name is not None:
                last_name, first_name = map(str.strip, name.split())

                mysql.query("UPDATE `users` SET `first_name` = %s, `last_name` = %s WHERE `id` = %s", (
                    first_name, last_name,
                    person["id"]
                ))

            mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                person["id"]
            ))

        else:
            print("Login failed")
            mysql.query("DELETE FROM `users` WHERE `id` = %s", (person["id"],))

    except Exception:
        print(format_exc())

    finally:
        print("Logout")
        del nts

    print()


if __name__ == "__main__":
    infinite()
