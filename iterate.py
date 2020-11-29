from MySQL.MySQL import MySQL
from datetime import datetime

from NetSchool import NetschoolUser


def main():
    mysql = MySQL("MySQL/config.json")

    people = mysql.query("SELECT * FROM `users`")

    sql = [
        "LOCK TABLES announcements WRITE;",
        "TRUNCATE TABLE `announcements`;"
    ]

    for person in people:

        print("Running for person | {} {}...".format(person["first_name"], person["last_name"]))

        nts = NetschoolUser(person["username"], person["password"])

        if nts.login():
            print("Login success")
        #     for author, title, date, text in nts.getAnnouncements():
        #         sql += "INSERT INTO `announcements` (`author`, `title`, `date`, `text`) VALUES ({}, {}, {}, {});\n".format(author, title, date, text)
        else:
            print("Login failed")

        nts.logout()
        print("Logout")

        del nts

        cur_daytime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (cur_daytime, person["id"]))

    sql.append("UNLOCK TABLES;")

    for request in sql:
        mysql.query(request)

    del mysql


if __name__ == "__main__":
    main()
