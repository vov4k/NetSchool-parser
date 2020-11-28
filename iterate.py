from MySQL.MySQL import MySQL
from datetime import datetime


def main():
    mysql = MySQL("MySQL/config.json")

    people = mysql.query("SELECT * FROM `users`")

    for person in people:

        print("Running for person | {} {}".format(person["first_name"], person["last_name"]))

        # TODO

        cur_daytime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mysql.query("UPDATE `users` SET `last_update` = %s WHERE `id` = %s", (cur_daytime, person["id"]))

    del mysql


if __name__ == "__main__":
    main()
