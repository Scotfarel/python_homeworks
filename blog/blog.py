import argparse
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

    def get_user_id_by_token(self, user_token):
        user_id = self._tokens_dict.get(user_token)
        if user_id is None:
            raise KeyError('Token is corrupted. Try to authenticate again.')
        return user_id

    def get_hash(self, sens_data):
        return hashlib.sha256((self._salt + sens_data).encode('utf-8')).hexdigest()

    def add_new_user(self, user_username, user_email, user_password):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM User WHERE Username=%s OR Email=%s"
            cursor.execute(sql, (user_username, user_email))
            if cursor.fetchone() is not None:
                raise ValueError(f'Username "{user_username}" or Email "{user_email}" are already taken')
            sql = "INSERT INTO User (Username, Email, Password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_username, user_email, self.get_hash(user_password)))
        self.db_connection.commit()

    def authenticate_user(self, user_email, user_password):
        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM User WHERE Email=%s AND Password=%s"
            cursor.execute(sql, (user_email, self.get_hash(user_password)))
            user_id_dict = cursor.fetchone()
        if user_id_dict is None:
            raise KeyError('Incorrect Login/Password pair. Please, try again')
        user_token = uuid.uuid4()
        user_id = user_id_dict['UserID']
        self._tokens_dict[user_token] = user_id

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
                raise ValueError(f'BlogName "{blog_name}" is already taken')
            sql = "INSERT INTO Blog (BlogDescription, UserID, BlogName) VALUES (%s, %s, %s)"
            cursor.execute(sql, (blog_description, user_id, blog_name))
        self.db_connection.commit()

    def edit_blog(self, user_token, blog_id, changed_name=None, changed_description=None):
        user_id = self.get_user_id_by_token(user_token)

        with self.db_connection.cursor() as cursor:
            sql = "SELECT UserID FROM Blog WHERE BlogID=%s"
            cursor.execute(sql, blog_id)
            blog_user_id = cursor.fetchone()

        if blog_user_id['UserID'] != user_id:
            raise ValueError('You don\'t have enough permission to edit someones blog. Verify your "blog_id"')

        with self.db_connection.cursor() as cursor:
            if changed_name is not None:
                sql = "SELECT UserID FROM Blog WHERE BlogName=%s"
                cursor.execute(sql, changed_name)
                if cursor.fetchone() is not None:
                    raise ValueError(f'BlogName "{changed_name}" is already taken')

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

        if blog_user_id['UserID'] != user_id:
            raise ValueError('You don\'t have enough permission to delete someones blog. Verify your "blog_id"')

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
            raise ValueError(f'No post with post_id {post_id}. Verify your "post_id"')

        if post_user_id['UserID'] != user_id:
            raise ValueError('You don\'t have enough permission to edit someones post. Verify your "post_id"')

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
            raise ValueError(f'No post with post_id {post_id}. Verify your "post_id"')

        if post_user_id['UserID'] != user_id:
            raise ValueError('You don\'t have enough permission to delete someones post. Verify your "post_id"')

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
                raise ValueError(f'No comment with comment_id {parent_id}. Verify your "parent_id"')

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
        return users_comments

    def get_new_user_token(self):
        fake = Faker()

        username, user_email, user_pwd = fake.name(), fake.email(), fake.password()
        self.add_new_user(username, user_email, user_pwd)
        user_token = self.authenticate_user(user_email, user_pwd)
        return user_token

    def fill_database(self):
        fake = Faker()

        filled_users = 1000
        filled_blogs = 100
        filled_posts = 10000
        filled_comments = 100000

        users = 0
        while users < filled_users:
            try:
                self.add_new_user(fake.name(), fake.email(), fake.password())
                users += 1
            except ValueError:
                continue

        blogs = 0
        while blogs < filled_blogs:
            try:
                user_token = self.get_new_user_token()
                self.create_blog(user_token,
                                 fake.word(ext_word_list=None),
                                 fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None))
                blogs += 1
            except ValueError or KeyError:
                continue

        posts = 0
        while posts < filled_posts:
            try:
                user_token = self.get_new_user_token()
                self.create_post(user_token,
                                 random.randint(1, filled_blogs),
                                 fake.text(max_nb_chars=200, ext_word_list=None),
                                 fake.bs())
                posts += 1
            except ValueError or KeyError:
                continue

        comments = 0
        while comments < filled_comments:
            try:
                user_token = self.get_new_user_token()
                self.add_comment(user_token,
                                 fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None),
                                 random.randint(1, filled_posts))
                comments += 1
            except ValueError or KeyError:
                continue


def create_args_parser():
    prs = argparse.ArgumentParser(description='Blog class to work with db')
    prs.add_argument('salt', help='String used in hashing')
    prs.add_argument('db_pwd', help='Pwd from current db')
    prs.add_argument('db_name', help='Name from current db')
    return prs


if __name__ == '__main__':
    parser = create_args_parser()
    args = parser.parse_args()

    blog = BlogApp(args.salt, args.db_pwd, args.db_name)

    # Use class methods here
