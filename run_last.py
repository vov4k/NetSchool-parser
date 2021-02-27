from MySQL import MySQL

from traceback import format_exc
from json import dumps as json_dumps, loads as json_loads
# from time import sleep
# from os import remove as os_remove
from os.path import exists as os_exists
import datetime

from nts_parser import NetSchoolUser


DOCPATH = 'doctmp'

UPDATE_TIMEOUT = datetime.timedelta(minutes=5)
SIM_HANDLING = 5


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


def school_year_weeks(year=None):
    if year is None:
        year = datetime.datetime.today().year
        if datetime.datetime.today().month < 9:
            year -= 1

    yield from week_period(
        datetime.date(year, 9, 1),
        datetime.date(year + 1, 6, 1)
    )


def school_year_weeks_from_now(year=None):
    if year is None:
        year = datetime.datetime.today().year
        if datetime.datetime.today().month < 9:
            year -= 1

    yield from week_period(
        (datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday())).date(),
        datetime.date(year + 1, 6, 1)
    )


def get_full_weekly_timetable(nts, monday, get_class=False, get_name=False):
    # monday -= datetime.timedelta(days=day.weekday())  # If monday is actually not monday

    result = {}

    try:
        class_, name_, weekly_timetable = nts.get_weekly_timetable_ext(date=monday, get_class=get_class, get_name=get_name)

        for day in weekly_timetable:

            # Be careful not to ruin the lesson order
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

    return class_, name_, result


def run_person(mysql, person):

    if person["last_update"] is not None and datetime.datetime.now() - person["last_update"] < UPDATE_TIMEOUT:
        return

    print("Running for person | {} {}...".format(person["first_name"], person["last_name"]))

    nts = NetSchoolUser(person["username"], person["password"], DOCPATH)

    try:

        name = None
        class_ = None

        if nts.login():
            print("Login success")

            # Announcements:
            try:
                print("Getting announcements...")
                name, announcements = nts.get_announcements(get_name=True)

                mysql.query("LOCK TABLES announcements WRITE;TRUNCATE TABLE `announcements`;")

                for author, title, date, text in announcements:
                    mysql.query(
                        "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES (%s, %s, %s, %s);",
                        (author, title, date, text)
                    )

                mysql.query("UNLOCK TABLES;")

                print("Got announcements")

            except Exception:
                print(format_exc())

            # Timetable:
            try:
                timetable = json_loads(mysql.query("SELECT `timetable` FROM `users` WHERE `id` = %s", format(person["id"]))[0]['timetable'])

                for date in list(timetable.keys()):
                    if datetime.datetime.strptime(date, "%Y-%m-%d").date() >= datetime.datetime.today().date():
                        del timetable[date]

                if person["last_update"] is None:
                    today = datetime.datetime.today()
                    monday = today - datetime.timedelta(days=today.weekday())
                    cur_period = week_period(monday, monday + datetime.timedelta(days=7))

                else:
                    cur_period = school_year_weeks_from_now()

                for week_start in cur_period:
                    print("Getting timetable for week starting with {}...".format(week_start))

                    new_class, new_name, weekly_timetable = get_full_weekly_timetable(nts, week_start, get_class=(class_ is None), get_name=(name is None))

                    name = new_name if name is None else name
                    class_ = new_class if class_ is None else class_

                    timetable.update(**weekly_timetable)

                mysql.query("UPDATE `users` SET `timetable` = %s WHERE `id` = %s", (json_dumps(timetable, ensure_ascii=False), person["id"]))

            except Exception:
                print(format_exc())

            # Diary:
            if person["last_update"] is not None:
                diary = {}

                try:
                    for week_start in school_year_weeks():
                        print("Getting diary for week starting with {}...".format(week_start))

                        new_class, new_name, weekly_diary = nts.get_diary(week_start, get_class=(class_ is None), get_name=(name is None), full=True)

                        name = new_name if name is None else name
                        class_ = new_class if class_ is None else class_

                        diary.update(**{key.strftime("%Y-%m-%d"): weekly_diary[key] for key in weekly_diary})

                    mysql.query("UPDATE `users` SET `diary` = %s WHERE `id` = %s", (json_dumps(diary, ensure_ascii=False), person["id"]))

                except Exception:
                    print(format_exc())

            # General info (first name, last name, last update):
            if name is not None:
                last_name, first_name = map(str.strip, name.split())

                mysql.query("UPDATE `users` SET `first_name` = %s, `last_name` = %s WHERE `id` = %s", (
                    first_name, last_name,
                    person["id"]
                ))

            if class_ is not None:
                mysql.query("UPDATE `users` SET `class` = %s WHERE `id` = %s", (
                    class_,
                    person["id"]
                ))

            mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (
                (datetime.datetime.now() - UPDATE_TIMEOUT).strftime("%Y-%m-%d %H:%M:%S") if person["last_update"] is None else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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


def run_last():
    if not os_exists(".run_person.lock"):
        with open(".run_person.lock", 'w'):
            pass

    mysql = None
    try:
        mysql = MySQL("config.json")

        with open(".run_person.lock", 'r', encoding="utf-8") as file:
            cur_running_ids = set(map(int, (line for line in file if line.strip())))

        if len(cur_running_ids) < SIM_HANDLING:

            person = mysql.query("SELECT * FROM `users`{} ORDER BY `last_update` LIMIT 1".format(
                (
                    " WHERE " +
                    " AND ".join("`id` != '{}'".format(user_id) for user_id in cur_running_ids)
                )
                if cur_running_ids else ""
            ))

            if person:
                user_id = person[0]['id']
                with open(".run_person.lock", 'a', encoding="utf-8") as file:
                    file.write('\n' + str(user_id))

                try:
                    run_person(mysql, person[0])
                except Exception:
                    pass

                with open(".run_person.lock", 'r', encoding="utf-8") as file:
                    cur_running_ids = set(map(int, (line for line in file if line.strip())))

                cur_running_ids.discard(user_id)

                with open(".run_person.lock", 'w', encoding="utf-8") as file:
                    file.write('\n'.join(map(str, cur_running_ids)))

    except Exception:
        print(format_exc())
        # sleep(10)

    finally:
        del mysql


if __name__ == "__main__":
    run_last()
