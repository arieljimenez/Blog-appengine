#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import jinja2
import hmac
import re
import cgi
import urllib2
import urllib
import json
import logging
import time

from collections import OrderedDict

from xml.dom import minidom

from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env    = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                  autoescape = True)

##########################################################################
########################################################## GLOBAL STUFF ##
##########################################################################

SECRET  = "_ArIeL=fRiSmAuRy#"
MOD_DATE_FORMAT = "%a %b %d %H:%M:%S %Y"

############################################################## DB STUFF ##

def get_dbkey(name = 'default'):
    return db.Key.from_path("blog-ariel", name)

class Blog_Posts(db.Model):
    title   = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    topic   = db.StringProperty(required = True)
    user    = db.StringProperty(required = True)
    state   = db.BooleanProperty(True)
    modified= db.DateTimeProperty(auto_now_add = True)

class Blog_Users(db.Model):
    user_name = db.StringProperty(required = True)
    user_pass = db.TextProperty(required = True)
    user_type = db.StringProperty(required = True)
    user_mail = db.StringProperty(required = False)
    siginup   = db.DateTimeProperty(auto_now_add = True)
    comments  = db.IntegerProperty(required = True)
    posts     = db.IntegerProperty(required = True)

########################################################## PUBLICS VOIDS #

def verify_pass(passw, verify):
    return passw == verify

def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and USER_RE.match(username)

def valid_user_pass(password):
    PASS_RE = re.compile(r"^.{3,20}$")
    return password and PASS_RE.match(password)

def valid_mail(email):
    EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
    return not email or EMAIL_RE.match(email)

def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return '%s|%s' % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]

    if h == make_secure_val(val):
        return val

def get_user_by_name(name):
    #users = db.GqlQuery("SELECT * FROM Blog_Users")
    # better check from cache

    blog_users = memcache.get("blog_users")

    if blog_users is None:
        make_cache()
        blog_users = memcache.get("blog_users")

    for key, value in blog_users.items():
        if value.user_name == name:
            return value


def insert_new_user(user_name, user_pass, user_mail=None):
    """Insert a new user in the db and returned it."""

    u = Blog_Users( parent = get_dbkey(),
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
        make_cache()
        blog_users = memcache.get("blog_users")

    blog_users[user_id] = u

    memcache.set("blog_users", blog_users)

    return u


def check_user(uid, upass):

    blog_users = memcache.get("blog_users")

    if blog_users is None:
        make_cache()
        blog_users = memcache.get("blog_users")

    if upass == blog_users[uid].user_pass:
        return True


def valid_cookie(cookie):
    user_id, pass_hash = cookie.split('|')

    if check_user(user_id, pass_hash):
        blog_users = memcache.get("blog_users")

        if blog_users is None:
            make_cache()
            blog_users = memcache.get("blog_users")

        return  blog_users[user_id]

def make_cache():
    ############ posts
    blog_posts = {}

    time_spend = time.time()
    posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1 ORDER BY modified ASC", get_dbkey())

    for post in posts:
        if not post.title in blog_posts:
            blog_posts[post.title] = {}

        v = len(blog_posts[post.title])

        blog_posts[post.title][v]= {"id" : str(post.key().id()),
                                    "title": post.title,
                                    "topic": post.topic,
                                    "content": post.content,
                                    "user": post.user,
                                    "modified": post.modified.strftime(MOD_DATE_FORMAT),
                                    "state": post.estate}

    memcache.set("blog_posts", blog_posts)
    logging.error("took %s caching all the posts " % (time.time() - time_spend))

    ############ users // page
    blog_users = {}
    time_spend = time.time()
    users = db.GqlQuery("SELECT * FROM Blog_Users WHERE ANCESTOR IS :1",  get_dbkey())


    for user in users:
         blog_users[str(user.key().id())] = user

    if len(blog_users) == 0:
        admin = Blog_Users( user_name="ariel",
                            user_pass= hash_str("ariel"),
                            user_type = "admin",
                            comments  = 0,
                            posts     = 0)
        admin.put()
        blog_users[str(admin.key().id())] =   admin

        logging.error("admin created")

    logging.error("took %s caching all the users " % (time.time() - time_spend))


    memcache.set("blog_users", blog_users)

def sana_html(texto):
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

############################################################################################################
###################################################### HANDLERS ############################################
############################################################################################################

class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def error(self, number):
        u = None
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if  not u:
                self.redirect("/login") # bad cookie
                return

        if number == 404:
            error = "The post that you looking for does not exist, try again bro or go <a href='/'>Home</a>."
        elif number == 500:
            error = "User does not exist or is currently invalid."
        else:
            error = "uuups, i think that you broke something."

        self.render("error.html", error=error, user=u)


###################################################################

class LoginHandler(Handler):
    def render_login(self, user="", userError="", passError="", next_url=""):
        self.render("login.html", user = user, userError = userError, passError = passError, next_url=next_url )

    def get(self):
        next_url = self.request.headers.get('referer', '/')
        user_cookie_str = self.request.cookies.get('user_id')

        if next_url == "/login":
            next_url = "/"

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if u: # the user is alredy login, redirect him to the main page
                self.redirect(str(next_url))

            else:
                self.write(valid_cookie(user_cookie_str))
        else:
            self.render_login(next_url=next_url)


    def post(self):
        userE   = ''
        passE   = ''

        user  = cgi.escape(self.request.get('username'), quote= True)
        passw = cgi.escape(self.request.get('password'), quote= True)

        next_url = self.request.get('next_url')

        if not valid_username(user):
            userE = "Not a valid username"

        if not valid_user_pass(passw):
            passE = "Not a valid pass"

        if valid_username(user) and valid_user_pass(passw):
            pass_hash = hash_str(passw)
            user_data = get_user_by_name(user)

            if user_data:
                if user_data.user_pass == pass_hash:
                    new_cookie_val = str(user_data.key().id()) + "|"+ pass_hash

                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % new_cookie_val)
                    self.redirect(str(next_url))

                else:
                    passE = "The pass is invalid, try again."
                    self.render_login(user, userE, passE)
            else:
                userE = "The user is invalid, try again with a valid user or <a href='/signup'>signup</a>."
                self.render_login(user, userE, passE)

        else:
            self.render_login(user, userE, passE)


class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect(str(next_url))



class SignUpHandler(Handler):
    def render_signup(self, user="", email="", userError="", passError="", verifyError="", mailError="", next_url=""):
        if next_url == "/signup":
            next_url = "/"

        self.render("signup.html",
                    user = user,
                    email = email,
                    userError = userError,
                    passError = passError,
                    verifyError = verifyError,
                    mailError = mailError,
                    next_url=next_url)

    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render_signup(next_url=next_url)

    def post(self):
        userE   = ''
        passE   = ''
        verifyE = ''
        mailE   = ''

        user  = cgi.escape(self.request.get('username'), quote= True)
        passw = cgi.escape(self.request.get('password'), quote= True)
        verify= cgi.escape(self.request.get('verify'), quote= True)
        email = cgi.escape(self.request.get('email'), quote= True)

        if not valid_username(user):
            userE = "Not a valid username"

        if not valid_user_pass(passw):
            passE = "Not a valid pass"

        if not verify_pass(passw, verify):
            verifyE = "The Passwords dont match!"

        if not valid_mail(email):
            mailE = "Not a valid email"

        if len(email) > 0:
            if valid_username(user) and valid_user_pass(passw) and verify_pass(passw, verify) and valid_mail(email):
                pass_hash = hash_str(passw)
                user_data = get_user_by_name(user)

                if user_data: #user exist?
                    userE = "That user already exists."
                    self.render_signup(user, email, userE, passE, verifyE)
                else:
                    #nope.. so, a new user :D
                    u = insert_new_user(user_name = user, user_pass = pass_hash, user_mail = email)
                    new_cookie = str("%s|%s" % (u.key().id(), u.user_pass))

                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % new_cookie)

                    self.redirect('/user/%s' % u.user_name)
            else:
                self.render_signup(user, email, userE, passE, verifyE, mailE)

        else: # without mail
            if valid_username(user) and valid_user_pass(passw) and verify_pass(passw, verify):

                pass_hash = hash_str(passw)
                user_data = get_user_by_name(user)

                if user_data: #user exist?
                    userE = "That user already exists."
                    self.render_signup(user, email, userE, passE, verifyE)

                else:
                    #nope.. so, a new user :D
                    u = insert_new_user(user_name = user, user_pass = pass_hash)

                    new_cookie = str("%s|%s" % (u.key().id(), u.user_pass))

                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % new_cookie)

                    # next_url = str(self.request.get('next_url'))
                    # self.redirect(next_url)
                    self.redirect('/user/%s' % u.user_name)
            else:
                self.render_signup(user, email, userE, passE, verifyE)

##########################################################################################################

class MainHandler(Handler):
    def render_post(self, post, user_type="anon", title="Home"):
        user_name = None
        u = None
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login") # bad cookie
                return

        if post:
            title = post["title"]

        self.render("blog.html",
                    post=post,
                    title=title,
                    user= u)


    def get(self, title="/"):

        blog_posts = memcache.get("blog_posts")

        if blog_posts is None:
            make_cache()
            blog_posts = memcache.get("blog_posts")

        if title in blog_posts: #
            post = blog_posts[title]
            post["content"] = sana_html(post["content"])
            self.render_post(post=post, mod=False)
            return

        elif title == "/":
            self.render_post(post=None)
            return

        else:
            self.error(404)
            # error = "The post that you looking for does not exist, try again bro or go <a href='/'>Home</a>."
            # self.render("error.html", error=error, user=None)


class UserPageHandler(Handler):
    def get(self, user):
        user_name = None
        u = None
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login") # bad cookie
                return

        user_data = get_user_by_name(user[1:])

        if user_data:
            title = "%s is profile " % user_data.user_name

            #totalposts = len(memcache.get("blog_posts"))
            totalposts = 50;

            self.render("profile.html",
                        title=title,
                        user = u,
                        user_profile = user_data,
                        totalposts=totalposts)
        else:
            self.error(500)
            # error = "User does not exist or is currently invalid."
            # self.render("error.html", error=error, user=None)


class NewPost(Handler):
    def get(self):
        pass


class PostHandler(Handler):
    def get(self):
        pass


class AdminPanel(Handler):
    def get(self):
        pass

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([('/',            MainHandler),
                               ('/login',       LoginHandler),
                               ('/logout',      LogoutHandler),
                               ('/signup',      SignUpHandler),
                               ('/user'+     PAGE_RE, UserPageHandler),
                               ('/adminpanel',  AdminPanel),
                               ('/posts/new'+ PAGE_RE, NewPost),
                               ('/posts'+ PAGE_RE, MainHandler),
                               (PAGE_RE, MainHandler),
                                ], debug=True)
