import pymysql


def create_db():
    database_server_ip = "localhost"  # IP address of the MySQL database server
    database_username = "newuser_gn"  # User name of the database server
    database_userpassword = "password_gn"  # Password for the database user
    database_name = "BlogDatabaseScript"  # Name of the database that is to be created
    char_set = "utf8mb4"  # Character set

    cursor = pymysql.cursors.DictCursor
    connection = pymysql.connect(host=database_server_ip,
                                 user=database_username,
                                 password=database_userpassword,
                                 charset=char_set,
                                 cursorclass=cursor)
    try:
        cursor = connection.cursor()
        sql = "CREATE DATABASE " + database_name
        cursor.execute(sql)
        connection.commit()

        sql = "USE " + database_name
        cursor.execute(sql)
        connection.commit()

        sql = "CREATE TABLE User (UserID INT NOT NULL PRIMARY KEY AUTO_INCREMENT, \
                                  Username VARCHAR(256) NOT NULL, \
                                  Email VARCHAR(256) NOT NULL, \
                                  Password VARCHAR(256) NOT NULL)"
        cursor.execute(sql)
        connection.commit()

        sql = "CREATE TABLE Blog (BlogID INT NOT NULL PRIMARY KEY AUTO_INCREMENT, \
                                  BlogDescription VARCHAR(1024), \
                                  UserID INT NOT NULL, \
                                  BlogName VARCHAR(256) NOT NULL)"
        cursor.execute(sql)
        connection.commit()

        sql = "CREATE TABLE Post (PostID INT NOT NULL PRIMARY KEY AUTO_INCREMENT, \
                                  UserID INT NOT NULL, \
                                  BlogID INT NOT NULL, \
                                  PostBody VARCHAR(1024) NOT NULL, \
                                  PostName VARCHAR(256) NOT NULL)"
        cursor.execute(sql)
        connection.commit()

        sql = "CREATE TABLE Comment (CommentID INT NOT NULL PRIMARY KEY AUTO_INCREMENT, \
                                     UserID INT NOT NULL, \
                                     CommentBody VARCHAR(1024) NOT NULL, \
                                     PostID INT NOT NULL, \
                                     ParentID INT)"
        cursor.execute(sql)
        connection.commit()

    finally:
        connection.close()


if __name__ == '__main__':
    create_db()
