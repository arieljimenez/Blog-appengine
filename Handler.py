import os
import webapp2
import jinja2
import hmac
import re
import cgi
import json
import logging
import time

from Blog_Users import Blog_Users
from Blog_Posts import Blog_Posts
from Comments import Comments

from collections import OrderedDict

from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env    = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                  autoescape = True)

SECRET  = "_ArIeL=fRiSmAuRy#"

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def error(self, number):
        u = self.validate_user()

        if number == 404:
            error = "The post that you looking for does not exist, try again bro or go <a href='/'>Home</a>."
        elif number == 500:
            error = "User does not exist or is currently invalid."
        else:
            error = "uuups, i think that you broke something."

        self.render("error.html", error=error, user=u)

    def verify_pass(self, passw, verify):
        return passw == verify

    def validate_user(self):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = self.valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login") # bad cookie
                return
            else:
                return u


########################
    def get_dbkey(self, name = 'default'):
        return db.Key.from_path("blog-ariel", name)

    def valid_username(self, username):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        return username and USER_RE.match(username)

    def valid_user_pass(self, password):
        PASS_RE = re.compile(r"^.{3,20}$")
        return password and PASS_RE.match(password)

    def valid_mail(self, email):
        EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
        return not email or EMAIL_RE.match(email)

    def hash_str(self, s):
        return hmac.new(SECRET, s).hexdigest()

    def make_secure_val(self, s):
        return '%s|%s' % (s, hash_str(s))

    def check_secure_val(self, h):
        val = h.split('|')[0]

        if h == self.make_secure_val(val):
            return val

    def get_user_by_name(self, name):

        blog_users = memcache.get("blog_users")

        if blog_users is None:
            self.make_cache()
            blog_users = memcache.get("blog_users")

        for key, value in blog_users.items():
            if value.user_name == name:
                return value


    def insert_new_user(self, user_name, user_pass, user_mail=None):
        """Insert a new user in the db and returned it."""

        u = Blog_Users( parent    = self.get_dbkey(),
                        user_name = user_name,
                        user_pass = str(user_pass),
                        user_mail = user_mail,
                        user_type = "user",
                        comments  = 0,
                        posts     = 0)
        u.put()

        user_id = str(u.key().id())

        blog_users = memcache.get("blog_users")

        if blog_users is None:
            self.make_cache()
            blog_users = memcache.get("blog_users")

        blog_users[user_id] = u

        memcache.set("blog_users", blog_users)

        return u


    def check_user(self, uid, upass):

        blog_users = memcache.get("blog_users")

        if blog_users is None:
            self.make_cache()
            blog_users = memcache.get("blog_users")

        if upass == blog_users[uid].user_pass:
            return True


    def valid_cookie(self, cookie):
        user_id, pass_hash = cookie.split('|')

        if self.check_user(user_id, pass_hash):
            blog_users = memcache.get("blog_users")

            if blog_users is None:
                self.make_cache()
                blog_users = memcache.get("blog_users")

            return  blog_users[user_id]

    def make_cache(self):
        ############ posts
        blog_posts = {}

        time_spend = time.time()
        posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1", self.get_dbkey())

        for p in posts:
            blog_posts[str(p.key().id())] = p

        memcache.set("blog_posts", blog_posts)
        logging.error("took %s caching all the %s posts " % (time.time() - time_spend, len(blog_posts)))

        ############ users // page
        blog_users = {}
        time_spend = time.time()
        users = db.GqlQuery("SELECT * FROM Blog_Users WHERE ANCESTOR IS :1",  self.get_dbkey())

        if not any(u.user_type == "admin" for u in users):
            logging.error("Ther is no admin, lets create one")

            admin = Blog_Users( parent    = self.get_dbkey(),
                                user_name = "admin",
                                user_pass = hash_str("159357"),
                                user_type = "admin",
                                comments  = 0,
                                posts     = 0)
            admin.put()
            blog_users[str(admin.key().id())] = admin

            logging.error("admin created")

        for user in users:
             blog_users[str(user.key().id())] = user

        logging.error("took %s caching all the %s users " % (time.time() - time_spend, len(blog_users)))

        memcache.set("blog_users", blog_users)

        time_spend = time.time() #in your marks....reeedy...GO!
        blog_comments = {}
        total_comments = 0

        comments = db.GqlQuery("SELECT * FROM Comments WHERE ANCESTOR IS :1",  self.get_dbkey())

        for comment in comments:
            total_comments += 1

            if not comment.post_title in blog_comments:
                blog_comments[comment.post_title] = { str(comment.key().id()) : comment }
            else:
                blog_comments[comment.post_title][str(comment.key().id())] = comment

        memcache.set("blog_comments", blog_comments)

        logging.error("took %s caching all the %s comments " % (time.time() - time_spend, len(blog_comments)))

        #rankings
        time_spend = time.time()
        self.calc_posts_statics()
        logging.error("took %s caching the posts rankings" % (time.time() - time_spend))

        total_activity = 0
        total_activity = len(blog_posts) + total_comments
        memcache.set("total_activity", total_activity)


    def sana_html(self, texto):
        texto = texto.replace("<script", "<nope")
        texto = texto.replace("</script>", "/nope")
        texto = texto.replace("</form>", "/nope")
        texto = texto.replace("</style>", "/nope")
        texto = texto.replace("()", "(nope)")
        texto = texto.replace("</html", "</not over yet")
        texto = texto.replace("<head>", "<cabeza>")
        texto = texto.replace("<iframe", "<iNope")
        texto = texto.replace("<input", "<nope")

        return texto

    def getPostbytitle(self, title, view = False):
        blog_posts = memcache.get("blog_posts")

        if blog_posts is None:
            self.make_cache()
            blog_posts = memcache.get("blog_posts")

        for key, value in blog_posts.iteritems():
            if value.title == title:

                if view:
                    value.views += 1
                    value.put() #update db

                    blog_posts[key] = value # update cache
                    memcache.set("blog_posts", blog_posts)

                return value


    def getCommentsbyTitle(self, title):
        blog_comments = memcache.get("blog_comments")

        if blog_comments is None:
            self.make_cache()
            blog_comments = memcache.get("blog_comments")

        if title in blog_comments:
            return blog_comments[title]


    def calc_posts_statics(self, calc="all"):

        if calc == "comments" or calc == "all":
            topten_comm_posts = []
            comments = memcache.get("blog_comments")

            comm_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1  ORDER BY comments DESC LIMIT 10",  self.get_dbkey())

            for post in comm_posts:
                if post.title in comments: ##corrects the ammount of comments
                    post.comments = len(comments[post.title])

                topten_comm_posts.append([post.title, post.comments, post])

            memcache.set("topten_comm_posts", topten_comm_posts)


        if calc == "views" or calc == "all":
            topten_view_posts = []
            view_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1  ORDER BY views DESC LIMIT 10",  self.get_dbkey())

            for post in view_posts:
                topten_view_posts.append([post.title, post.views, post])

            memcache.set("topten_view_posts", topten_view_posts)


    def setDisablePost(self, title_id):
        posts = memcache.get("blog_posts")
        post = posts[title_id]
        post.state = not post.state
        post.put()

        self.calc_posts_statics("comments")
        memcache.set("blog_posts", posts)
        return post

    def update_comment(self, comment_id, updatedComment):
        comment = Comments.get_by_id(int(comment_id), self.get_dbkey())
        comment.post_comment = updatedComment
        comment.put()

        blog_comments = memcache.get("blog_comments")
        blog_comments[comment.post_title][comment_id] = comment
        memcache.set("blog_comments", blog_comments)

    def get_comments_by_user(self, user):
        comments = memcache.get("blog_comments")
        matched_comments = {}

        for title, comment_id in comments.iteritems():
            for key, comment in comment_id.iteritems():
                if comment.user_name == user:
                    matched_comments[comment.created.strftime("%y-%m-%d %H:%M:%S.%f")] = {"title"   : comment.post_title,
                                                                                          "comment" : comment.post_comment,
                                                                                          "created" : comment.created.strftime("%b %d, %Y")}
        return matched_comments

