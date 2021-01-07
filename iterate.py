from MySQL import MySQL
import datetime

from json import dumps

from NetSchool import NetSchoolUser

from traceback import format_exc

DOCPATH = 'doctmp'


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

    del mysql


def get_full_weekly_timetable(nts, day, get_name=False):
    monday = day - datetime.timedelta(days=day.weekday())

    result = {}

    try:
        weekly_timetable = nts.get_weekly_timetable(date=monday)

        for day_index, day in enumerate(day_period(monday, monday + datetime.timedelta(days=7))):
            if get_name:
                name, daily_timetable = nts.get_daily_timetable(date=day, get_name=True)
            else:
                daily_timetable = nts.get_daily_timetable(date=day)

            if weekly_timetable[day_index] is not None and daily_timetable is not None:
                daily_timetable.sort(key=lambda item: 0 if item[0] == 'lesson' else 1 if item[0] == 'vacation' else 2)

                for item in daily_timetable:
                    item[1][0] = item[1][0].strftime("%Y-%m-%d %H:%M:%S")
                    item[1][1] = item[1][1].strftime("%Y-%m-%d %H:%M:%S")

                for i in range(len(weekly_timetable[day_index])):
                    if weekly_timetable[day_index][i] is None:
                        daily_timetable.insert(i, None)

                # Remove None at the end of lessons
                for i in range(len(weekly_timetable[day_index]) - 1, -1, -1):
                    if daily_timetable[i] is not None:
                        break
                    del daily_timetable[i]

                result[day.strftime("%Y-%m-%d")] = daily_timetable

    except Exception:
        print(format_exc())
        for day in day_period(monday, monday + datetime.timedelta(days=7)):
            result[day.strftime("%Y-%m-%d")] = None

    if get_name:
        return name, result
    return result


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
                    cur_period = week_period(monday, monday + datetime.timedelta(days=7))

                else:
                    cur_period = every_school_year_week()

                for week_start in cur_period:
                    print("Getting timetable for week starting with {}...".format(week_start))

                    if name is None:
                        name, weekly_timetable = get_full_weekly_timetable(nts, week_start, get_name=True)
                    else:
                        weekly_timetable = get_full_weekly_timetable(nts, week_start, get_name=False)

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
