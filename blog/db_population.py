import random
from faker import Faker

from blog import BlogApp, create_args_parser


def get_user_token(tokens_list):
    user_token = random.choice(tokens_list)
    return user_token


def fill_database(db_to_fill):
    fake = Faker()

    filled_users = 1000
    filled_blogs = 100
    filled_posts = 10000
    filled_comments = 100000

    tokens_list = []

    users = 0
    while users < filled_users:
        try:
            user_username, user_email, user_pwd = fake.name(), fake.email(), fake.password()
            db_to_fill.add_new_user(user_username, user_email, user_pwd)
            user_token = db_to_fill.authenticate_user(user_email, user_pwd)
            tokens_list.append(user_token)
            users += 1
        except ValueError:
            continue

    blogs = 0
    while blogs < filled_blogs:
        try:
            user_token = get_user_token(tokens_list)
            print(user_token)
            db_to_fill.create_blog(user_token,
                             fake.word(ext_word_list=None),
                             fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None))
            blogs += 1
        except (ValueError or KeyError):
            continue

    posts = 0
    while posts < filled_posts:
        try:
            user_token = get_user_token(tokens_list)
            db_to_fill.create_post(user_token,
                             random.randint(1, filled_blogs),
                             fake.text(max_nb_chars=200, ext_word_list=None),
                             fake.bs())
            posts += 1
        except (ValueError or KeyError):
            continue

    comments = 0
    while comments < filled_comments:
        try:
            user_token = get_user_token(tokens_list)
            db_to_fill.add_comment(user_token,
                             fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None),
                             random.randint(1, filled_posts))
            comments += 1
        except (ValueError or KeyError):
            continue


if __name__ == "__main__":
    parser = create_args_parser()
    args = parser.parse_args()

    blog = BlogApp(args.salt, args.db_pwd, args.db_name)
    fill_database(blog)
