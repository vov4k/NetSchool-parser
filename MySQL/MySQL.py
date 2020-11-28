from json import load as json_load
import pymysql.cursors


class MySQL:
    def __init__(self, config_path):
        with open(config_path, 'r', encoding="utf-8") as config_file:
            config = json_load(config_file, encoding="utf-8")

        self.host = config["host"]
        self.user = config["user"]
        self.password = config["password"]
        self.db = config["database"]
        # self.charset = config["charset"]

        self.connection = pymysql.connect(host=self.host,
                                          user=self.user,
                                          password=self.password,
                                          db=self.db,
                                          cursorclass=pymysql.cursors.DictCursor,
                                          autocommit=True)

    def query(self, sql, args=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, args)
            result = cursor.fetchall()

        return result

    def __del__(self):
        self.close()

    def close(self):
        self.connection.close()


def main():
    mysql = MySQL("config.json")
    print(mysql.query("SELECT * FROM `users`"))


if __name__ == "__main__":
    main()
