from MySQL import MySQL

from traceback import format_exc
from json import dumps as json_dumps, loads as json_loads
# from time import sleep
# from os import remove as os_remove
from os.path import exists as os_exists
import datetime

from nts_parser import NetSchoolUser


DOCPATH = 'doctmp'

PROCESS_KILL_TIMOUT = datetime.timedelta(minutes=10)
SIM_HANDLING = 7


def get_update_timeout(person):
    if person['last_visit'] is None:
        return datetime.timedelta(), datetime.timedelta()

    update_timeout = (((datetime.datetime.now() - person['last_visit']).seconds / 86400) ** 2) / 2 + 1
    return datetime.timedelta(hours=update_timeout / 12), datetime.timedelta(hours=update_timeout)


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
    class_, name_ = None, None

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

    fast_update = person["last_update"] is None
    full_update = not fast_update and (
        person["last_full_update"] is None or (datetime.datetime.now() - person["last_full_update"] > get_update_timeout(person)[1])
    )
    ordinary_update = (
        person["last_update"] is not None and datetime.datetime.now() - person["last_update"] > get_update_timeout(person)[0]
    )

    if not (fast_update or full_update or ordinary_update):
        return

    print("Running \"{}\" for person | {}...".format(
        "fast_update" if fast_update else "full_update" if full_update else "ordinary_update",
        person["username"]
    ))

    nts = NetSchoolUser(person["username"], person["password"], DOCPATH)

    try:
        name = None
        class_ = None

        login_status = nts.login()

        if login_status:
            print("Login success")

            # Announcements:
            try:
                if not fast_update:
                    print("Getting announcements...")
                    name, announcements = nts.get_announcements(get_name=True)

                    mysql.query("LOCK TABLES announcements WRITE;TRUNCATE TABLE `announcements`;")

                    for author, title, date, text in announcements:
                        mysql.query(
                            "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES (%s, %s, %s, %s);",
                            (author, title, date, text)
                        )

                    mysql.query("UNLOCK TABLES;")

            except Exception:
                print(format_exc())

            # Timetable:
            try:
                timetable = {}

                if fast_update:
                    today = datetime.datetime.today()
                    monday = today - datetime.timedelta(days=today.weekday())
                    cur_period = week_period(monday, monday + datetime.timedelta(days=7))

                elif full_update:
                    cur_period = school_year_weeks()

                else:
                    try:
                        timetable = {
                            date: value for date, value in (
                                json_loads(mysql.query("SELECT `timetable` FROM `users` WHERE `id` = %s", format(person["id"]))[0]["timetable"]).items()
                            ) if datetime.datetime.strptime(date, "%Y-%m-%d").date() < (datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday())).date()
                        }
                        cur_period = school_year_weeks_from_now()

                    except Exception:
                        print(format_exc())
                        timetable = {}
                        cur_period = school_year_weeks()

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
            try:
                if not fast_update:
                    diary = {}

                    for week_start in school_year_weeks():
                        print("Getting diary for week starting with {}...".format(week_start))

                        new_class, new_name, weekly_diary = nts.get_diary(week_start, get_class=(class_ is None), get_name=(name is None), full=True)

                        name = new_name if name is None else name
                        class_ = new_class if class_ is None else class_

                        diary.update(**{key.strftime("%Y-%m-%d"): weekly_diary[key] for key in weekly_diary})

                    mysql.query("UPDATE `users` SET `diary` = %s WHERE `id` = %s", (json_dumps(diary, ensure_ascii=False), person["id"]))

            except Exception:
                print(format_exc())

            # General info (name, last update time):
            if name is not None:
                if len(name.split()) == 2:
                    name = ' '.join(name.split()[::-1])

                mysql.query("UPDATE `users` SET `name` = %s WHERE `id` = %s", (
                    name, person["id"]
                ))

            if class_ is not None:
                mysql.query("UPDATE `users` SET `class` = %s WHERE `id` = %s", (
                    class_,
                    person["id"]
                ))

            mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (

                (datetime.datetime.now() - datetime.timedelta(hours=8760)).strftime("%Y-%m-%d %H:%M:%S")
                if person["last_update"] is None else
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                person["id"]
            ))

            if full_update and not fast_update:
                mysql.query("UPDATE `users` SET `last_full_update` = %s WHERE `id` = %s", (
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    person["id"]
                ))

        elif login_status is not None:  # if login_status == False
            print("Login failed")
            mysql.query("DELETE FROM `users` WHERE `id` = %s", (person["id"],))

    except Exception:
        print(format_exc())

    finally:
        print("Logout")
        del nts

    print()


def run_last():

    def get_cur_running():
        with open(".run_person.lock", 'r', encoding="utf-8") as file:
            cur_running = {
                int(line.split()[0]): float(line.split()[1])
                for line in file if line.strip() and datetime.datetime.now() - datetime.datetime.fromtimestamp(float(line.split()[1])) < PROCESS_KILL_TIMOUT
            }

        return cur_running

    def set_cur_running(cur_running):
        with open(".run_person.lock", 'w', encoding="utf-8") as file:
            file.write('\n'.join("{} {}".format(key, value) for key, value in cur_running.items()))

    if not os_exists(".run_person.lock"):
        with open(".run_person.lock", 'w'):
            pass

    mysql = None
    try:
        mysql = MySQL("config.json")

        cur_running = get_cur_running()

        if len(cur_running) < SIM_HANDLING:

            person = mysql.query(
                """
                    SELECT * FROM `users` WHERE

                    (
                        `last_visit` IS NULL OR

                        UNIX_TIMESTAMP(`last_update`) + (

                            POW((UNIX_TIMESTAMP() - UNIX_TIMESTAMP(`last_visit`)) / 86400, 2) / 2 + 1
                        
                        ) / 12 * 3600 < UNIX_TIMESTAMP(NOW())
                    )

                    {} ORDER BY

                    UNIX_TIMESTAMP(`last_update`) + (
                    
                        POW((UNIX_TIMESTAMP() - UNIX_TIMESTAMP(`last_visit`)) / 86400, 2) / 2 + 1

                    ) / 12 * 3600

                    ASC LIMIT 1
                """.format(
                    (
                        "AND " + " AND ".join("`id` != '{}'".format(user_id) for user_id in cur_running)
                    )
                    if cur_running else ""
                )
            )

            if person:
                user_id = person[0]['id']
                cur_running[user_id] = datetime.datetime.now().timestamp()

                set_cur_running(cur_running)

                try:
                    run_person(mysql, person[0])
                except Exception:
                    print(format_exc())

                cur_running = get_cur_running()

                if user_id in cur_running:
                    del cur_running[user_id]

                set_cur_running(cur_running)

    except Exception:
        print(format_exc())
        # sleep(10)

    finally:
        del mysql


if __name__ == "__main__":
    run_last()
