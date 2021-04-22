from json import load as json_load
import pymysql.cursors
from pymysql.constants import CLIENT


class MySQL:
    def __init__(self, config_path):
        with open(config_path, 'r', encoding="utf-8") as config_file:
            config = json_load(config_file, encoding="utf-8")

        self.host = config["db_hostname"]
        self.user = config["db_username"]
        self.password = config["db_password"]
        self.db = config["db_name"]
        # self.charset = config["charset"]

        self.connection = pymysql.connect(host=self.host,
                                          user=self.user,
                                          password=self.password,
                                          db=self.db,
                                          cursorclass=pymysql.cursors.DictCursor,
                                          autocommit=False,
                                          client_flag=CLIENT.MULTI_STATEMENTS)

    def __del__(self):
        self.commit()
        self.close()

    def query(self, sql, args=None):
        with self.connection.cursor() as cursor:
            rows_num = cursor.execute(sql, args)

        return rows_num

    def fetch(self, sql, args=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, args)
            data = cursor.fetchall()

        return data

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def main():
    mysql = MySQL("../config.json")
    print(mysql.query("SELECT * FROM `users`"))


if __name__ == "__main__":
    main()
