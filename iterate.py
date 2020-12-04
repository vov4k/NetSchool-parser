from MySQL import MySQL
from datetime import datetime

from NetSchool import NetSchoolUser

DOCPATH = 'doctmp'


def infinite():
    while True:
        onetime()


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

        cur_daytime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:

            if nts.login():
                print("Login success")
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
                        pass
            else:
                print("Login failed")

            nts.logout()
            print("Logout\n")

            mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (cur_daytime, person["id"]))

        except Exception:
            pass

        del nts

    for request in announcements_sql + ["UNLOCK TABLES;"]:
        mysql.query(request)

    del mysql


if __name__ == "__main__":
    onetime()
