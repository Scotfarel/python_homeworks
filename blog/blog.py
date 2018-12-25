import argparse
import sys
import hashlib
import uuid
import random
import pymysql.cursors
from faker import Faker


class BlogApp:
    def __init__(self, salt, db_pwd, db_name):
        self._salt = salt
        self._tokens_dict = {}
        self._comments_thread = []
        self.db_connection = pymysql.connect(host='localhost',
                                             user='BlogApp_User',
                                             password=db_pwd,
                                             db=db_name,
                                             charset='utf8mb4',
                                             cursorclass=pymysql.cursors.DictCursor)

    def __del__(self):
        self.db_connection.close()

    @property
    def get_salt(self):
        return self._salt

    @property
    def get_tokens_dict(self):
        return self._tokens_dict

    def get_user_id_by_token(self, user_token):
        user_id = self.get_tokens_dict.get(user_token)
        if user_id is None:
            raise KeyError('Incorrect User Token')
        return user_id

    def get_hash(self, sens_data):
        return hashlib.sha256((self.get_salt + sens_data).encode('utf-8')).hexdigest()

    def add_new_user(self, user_username, user_email, user_password):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM User WHERE Username=%s OR Email=%s"
            cursor.execute(sql, (user_username, user_email))
            if cursor.fetchone() is not None:
                raise ValueError('Username Or Email Are Already Taken')
            sql = "INSERT INTO User (Username, Email, Password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_username, user_email, self.get_hash(user_password)))
        self.db_connection.commit()

    def authenticate_user(self, user_email, user_password):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM User WHERE Email=%s AND Password=%s"
            cursor.execute(sql, (user_email, self.get_hash(user_password)))
            user_id_dict = cursor.fetchone()
        if user_id_dict is None:
            raise KeyError('Incorrect Login/Password Pair. Please, Try Again')
        user_token = uuid.uuid4()
        user_id = user_id_dict.get('UserID')
        self.get_tokens_dict[user_token] = user_id

        return user_token

    def get_users_list(self):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT Username FROM User"
            cursor.execute(sql)
            users_list = cursor.fetchall()
        return users_list

    def get_auth_user_blog_list(self, user_token):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT BlogID, BlogName, BlogDescription FROM Blog WHERE UserID=%s"
            cursor.execute(sql, user_id)
            auth_user_blog_list = cursor.fetchall()
        return auth_user_blog_list

    def get_blog_list(self):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT BlogName, BlogDescription FROM Blog"
            cursor.execute(sql)
            blog_list = cursor.fetchall()
        return blog_list

    def create_blog(self, user_token, blog_name, blog_description):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Blog WHERE BlogName=%s"
            cursor.execute(sql, blog_name)
            if cursor.fetchone() is not None:
                raise ValueError('BlogName Are Already Taken')
            sql = "INSERT INTO Blog (BlogDescription, UserID, BlogName) VALUES (%s, %s, %s)"
            cursor.execute(sql, (blog_description, user_id, blog_name))
        self.db_connection.commit()

    def edit_blog(self, user_token, blog_id, changed_name=None, changed_description=None):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Blog WHERE BlogID=%s"
            cursor.execute(sql, blog_id)
            blog_user_id = cursor.fetchone()

        if blog_user_id.get('UserID') != user_id:
            raise ValueError('You Don\'t Have Enough Permission To Edit Someones Blog')

        with self.db_connection.cursor() as cursor:
            if changed_name is not None:
                sql = "SELECT UserID FROM Blog WHERE BlogName=%s"
                cursor.execute(sql, changed_name)
                if cursor.fetchone() is not None:
                    raise ValueError('BlogName Are Already Taken')

                sql = "UPDATE Blog SET BlogName=%s WHERE BlogID=%s"
                cursor.execute(sql, (changed_name, blog_id))

            if changed_description is not None:
                sql = "UPDATE Blog SET BlogDescription=%s WHERE BlogID=%s"
                cursor.execute(sql, (changed_description, blog_id))
        self.db_connection.commit()

    def delete_blog(self, blog_id, user_token):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Blog WHERE BlogID=%s"
            cursor.execute(sql, blog_id)
            blog_user_id = cursor.fetchone()

        if blog_user_id.get('UserID') != user_id:
            raise ValueError('You Don\'t Have Enough Permission To Delete Someones Blog')

        with self.db_connection.cursor() as cursor:
            sql = "DELETE FROM Blog WHERE BlogID=%s"
            cursor.execute(sql, blog_id)
        self.db_connection.commit()

    def create_post(self, user_token, blog_id, post_body, post_name):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "INSERT INTO Post (UserID, BlogID, PostBody, PostName) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, blog_id, post_body, post_name))
        self.db_connection.commit()

    def edit_post(self, user_token, post_id, changed_name=None, changed_body=None):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Post WHERE PostID=%s"
            cursor.execute(sql, post_id)
            post_user_id = cursor.fetchone()
        if post_user_id is None:
            raise ValueError('There Is No Your Post With This post_id')

        if post_user_id.get('UserID') != user_id:
            raise ValueError('You Don\'t Have Enough Permission To Edit Someones Post')

        with self.db_connection.cursor() as cursor:
            if changed_name is not None:
                sql = "UPDATE Post SET PostName=%s WHERE PostID=%s"
                cursor.execute(sql, (changed_name, post_id))
            if changed_body is not None:
                sql = "UPDATE Post SET PostBody=%s WHERE PostID=%s"
                cursor.execute(sql, (changed_body, post_id))
        self.db_connection.commit()

    def delete_post(self, user_token, post_id):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Post WHERE PostID=%s"
            cursor.execute(sql, post_id)
            post_user_id = cursor.fetchone()

        if post_user_id is None:
            raise ValueError('There Is No Your Post With This post_id')

        if post_user_id.get('UserID') != user_id:
            raise ValueError('You Don\'t Have Enough Permission To Delete Someones Blog')

        with self.db_connection.cursor() as cursor:
            sql = "DELETE FROM Post WHERE PostID=%s"
            cursor.execute(sql, post_id)
        self.db_connection.commit()

    def add_comment(self, user_token, comment_body, post_id, parent_id=None):
        user_id = self.get_user_id_by_token(user_token)

        if parent_id is None:
            with self.db_connection.cursor() as cursor:
                sql = "INSERT INTO Comment (UserID, CommentBody, PostID) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, comment_body, post_id))
            self.db_connection.commit()

        else:
            with self.db_connection.cursor() as cursor:
                sql = "SELECT CommentID FROM Comment WHERE PostID=%s"
                cursor.execute(sql, post_id)
                result = cursor.fetchall()

            if result is None:
                raise ValueError('There Is No Comment With This comment_id')

            for comment in result:
                if parent_id == comment.get('CommentID'):
                    with self.db_connection.cursor() as cursor:
                        sql = "INSERT INTO Comment (UserID, CommentBody, PostID, ParentID) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (user_id, comment_body, post_id, parent_id))
                    break
            self.db_connection.commit()

    def get_user_comments(self, user_token):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT CommentID, CommentBody FROM Comment WHERE UserID=%s"
            cursor.execute(sql, user_id)
            user_comments = cursor.fetchall()
        return user_comments

    def get_comments_thread(self, comment_id):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT CommentID, CommentBody FROM Comment WHERE ParentID=%s"
            cursor.execute(sql, comment_id)
            reply_comments = cursor.fetchall()

        if reply_comments is None:
            return self._comments_thread

        for comment in reply_comments:
            if comment not in self._comments_thread:
                self._comments_thread.append(comment)
            self.get_comments_thread(comment.get('CommentID'))

    def get_users_comments_from_blog(self, blog_id, *users_id):
        users_comments = []
        for user in users_id:
            with self.db_connection.cursor() as cursor:
                sql = "SELECT CommentID, CommentBody FROM Comment WHERE ParentID=%s AND BlogID=%s"
                cursor.execute(sql, user, blog_id)
                reply_comments = cursor.fetchall()
            if reply_comments is None:
                continue
            users_comments.append(reply_comments)
        if len(users_comments) == 0:
            raise ValueError('No Requested Comments')
        return users_comments

    def fill_database(self):
        fake = Faker()

        n_users = 1000
        n_blogs = 100
        n_posts = 10000
        n_comments = 100000

        for user in range(n_users):
            try:
                self.add_new_user(fake.name(), fake.email(), fake.password())
            except ValueError:
                n_users += 1
                continue

        for blog in range(n_blogs):
            try:
                username, user_email, user_pwd = fake.name(), fake.email(), fake.password()
                self.add_new_user(username, user_email, user_pwd)
                user_token = self.authenticate_user(user_email, user_pwd)
                self.create_blog(user_token,
                                 fake.word(ext_word_list=None),
                                 fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None))
            except ValueError:
                n_blogs += 1
                continue
            except KeyError:
                n_blogs += 1
                continue

        for post in range(n_posts):
            try:
                username, user_email, user_pwd = fake.name(), fake.email(), fake.password()
                self.add_new_user(username, user_email, user_pwd)
                user_token = self.authenticate_user(user_email, user_pwd)
                self.create_post(user_token,
                                 random.randint(1, n_blogs),
                                 fake.text(max_nb_chars=200, ext_word_list=None),
                                 fake.bs())
            except ValueError:
                n_posts += 1
                continue
            except KeyError:
                n_posts += 1
                continue

        for comment in range(n_comments):
            try:
                username, user_email, user_pwd = fake.name(), fake.email(), fake.password()
                self.add_new_user(username, user_email, user_pwd)
                user_token = self.authenticate_user(user_email, user_pwd)
                self.add_comment(user_token,
                                 fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None),
                                 random.randint(1, n_posts))
            except ValueError:
                n_comments += 1
                continue
            except KeyError:
                n_comments += 1
                continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='These are args from env')
    parser.add_argument('salt', help='String used in hashing')
    parser.add_argument('db_pwd', help='Pwd from current db')
    parser.add_argument('db_name', help='Name from current db')
    args = parser.parse_args(sys.argv[1:])

    blog = BlogApp(args.salt, args.db_pwd, args.db_name)

    # Use class methods here
