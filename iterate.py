from MySQL import MySQL

from traceback import format_exc
from json import dumps
from time import sleep
import datetime

from NetSchool import NetSchoolUser


DOCPATH = 'doctmp'

MINUTES_5 = datetime.timedelta(minutes=5)


def week_period(day_start, day_end):
    day_start -= datetime.timedelta(days=day_start.weekday())
    day_end -= datetime.timedelta(days=day_start.weekday())

    for i in range((day_end - day_start).days // 7):
        yield day_start + datetime.timedelta(weeks=i)


def day_period(day_start, day_end):
    for i in range((day_end - day_start).days):
        yield day_start + datetime.timedelta(days=i)


# def every_school_year_day(year=None):
#     if year is None:
#         year = datetime.datetime.today().year
#         if datetime.datetime.today().month < 9:
#             year -= 1

#     yield from day_period(
#         datetime.date(year, 9, 1),
#         datetime.date(year + 1, 6, 1)
#     )


def every_school_year_week(year=None):
    if year is None:
        year = datetime.datetime.today().year
        if datetime.datetime.today().month < 9:
            year -= 1

    yield from week_period(
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
        # break  # Debug

    del mysql


def get_full_weekly_timetable(nts, monday, get_name=False):
    # monday -= datetime.timedelta(days=day.weekday())  # If monday is actually not monday

    result = {}

    try:
        _, _name, weekly_timetable = nts.get_weekly_timetable_ext(date=monday, get_name=get_name)

        for day in weekly_timetable:

            weekly_timetable[day].sort(key=lambda item: 0 if item["type"] == "lesson" else 1 if item["type"] == "vacation" else 2)

            for item in weekly_timetable[day]:
                if "start" in item:
                    item["start"] = item["start"].strftime("%Y-%m-%d %H:%M:%S")

                if "end" in item:
                    item["end"] = item["end"].strftime("%Y-%m-%d %H:%M:%S")

            # Remove None at the end of lessons
            i = len(weekly_timetable[day]) - 1
            while i >= 0 and weekly_timetable[day][i]["type"] != "lesson":
                i -= 1
            while i >= 0 and weekly_timetable[day][i]["name"] is None:
                del weekly_timetable[day][i]
                i -= 1

            result[day.strftime("%Y-%m-%d")] = [
                [
                    item["type"],
                    item["name"],
                    item["start"] if "start" in item else None,
                    item["end"] if "end" in item else None
                ]
                for item in weekly_timetable[day]
            ]

    except Exception:
        print(format_exc())

        for day in day_period(monday, monday + datetime.timedelta(days=7)):
            result[day.strftime("%Y-%m-%d")] = None

    return _name, result


def run_person(mysql, person):

    if datetime.datetime.now() - person["last_update"] < MINUTES_5:
        sleep(5)
        return

    print("Running for person | {} {}...".format(person["first_name"], person["last_name"]))

    nts = NetSchoolUser(person["username"], person["password"], DOCPATH)

    name = None

    try:

        if nts.login():
            print("Login success")

            # Announcements:
            try:
                announcements_sql = [
                    "LOCK TABLES announcements WRITE;",
                    "TRUNCATE TABLE `announcements`;"
                ]

                name, announcements = nts.get_announcements(get_name=True)
                print("Got announcements")
                for author, title, date, text in announcements:
                    announcements_sql.append(
                        "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES (\"{}\", \"{}\", \"{}\", \"{}\");".format(author, title, date, text)
                    )

                announcements_sql.append("UNLOCK TABLES;")
                mysql.query("".join(announcements_sql))

            except Exception:
                print(format_exc())

            # Timetable:
            timetable = {}
            try:
                if person["last_update"] is None:
                    today = datetime.datetime.today()
                    monday = today - datetime.timedelta(days=today.weekday())
                    cur_period = week_period(monday, monday + datetime.timedelta(days=7))

                else:
                    cur_period = every_school_year_week()

                for week_start in cur_period:
                    print("Getting timetable for week starting with {}...".format(week_start))

                    if name is None:
                        name, weekly_timetable = get_full_weekly_timetable(nts, week_start, get_name=True)
                    else:
                        _, weekly_timetable = get_full_weekly_timetable(nts, week_start)

                    timetable.update(**weekly_timetable)

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
