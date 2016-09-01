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
import httplib

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
    comments= db.IntegerProperty()
    views   = db.IntegerProperty()

class Blog_Users(db.Model):
    user_name = db.StringProperty(required = True)
    user_pass = db.TextProperty(required = True)
    user_type = db.StringProperty(required = True)
    user_mail = db.StringProperty(required = False)
    siginup   = db.DateTimeProperty(auto_now_add = True)
    comments  = db.IntegerProperty(required = True)
    posts     = db.IntegerProperty(required = True)

class Comments(db.Model):
    user_id     = db.IntegerProperty(required = True)
    user_name   = db.StringProperty(required = True)
    post_id     = db.IntegerProperty(required = True)
    post_title  = db.StringProperty(required = True)
    post_comment= db.TextProperty(required = True)
    state       = db.BooleanProperty(required = True)
    created     = db.DateTimeProperty(auto_now_add = True)

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
    posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1", get_dbkey())

    for p in posts:
        blog_posts[str(p.key().id())] = p

    memcache.set("blog_posts", blog_posts)
    logging.error("took %s caching all the %s posts " % (time.time() - time_spend, len(blog_posts)))

    ############ users // page
    blog_users = {}
    time_spend = time.time()
    users = db.GqlQuery("SELECT * FROM Blog_Users WHERE ANCESTOR IS :1",  get_dbkey())

    if not any(u.user_type == "admin" for u in users):
        logging.error("Ther is no admin, lets create one")

        admin = Blog_Users( parent = get_dbkey(),
                            user_name="Admin",
                            user_pass= hash_str("159357"),
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

    # COMMENTS DOC
    # comments { idpost : { post_title : { comment_id : comment_obj }}}             struct
    # comments[idpost][post_title][idcomment]                                       get
    # comments[idpost][post_title][idcomment] = obj_comment                         set

    time_spend = time.time() #in your marks....reeedy...GO!
    blog_comments = {}

    comments = db.GqlQuery("SELECT * FROM Comments WHERE ANCESTOR IS :1",  get_dbkey())

    for comment in comments:
        if not comment.post_id in blog_comments:
            blog_comments[str(comment.post_id)] = { comment.post_title : { str(comment.key().id()) : comment } }
            #blog_comments[comment.post_id][comment.post_title] = { comment.key().id(): comment }
        else:
            blog_comments[comment.post_id][comment.post_title][comment.key().id()] = comment

    memcache.set("blog_comments", blog_comments)

    logging.error("took %s caching all the %s comments " % (time.time() - time_spend, len(blog_comments)))

    #rankings
    time_spend = time.time()

    calc_posts_statics()

    logging.error("took %s caching the posts rankings" % (time.time() - time_spend))



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

def getPostbytitle(title, view = False):
    blog_posts = memcache.get("blog_posts")

    if blog_posts is None:
        make_cache()
        blog_posts = memcache.get("blog_posts")

    for key, value in blog_posts.iteritems():
        if value.title == title:

            if view:
                value.views += 1
                value.put() #update db

                blog_posts[key] = value # update cache
                memcache.set("blog_posts", blog_posts)

            return value


def getCommentsbyTitle(title):
    blog_comments = memcache.get("blog_comments")

    if blog_comments is None:
        make_cache()
        blog_comments = memcache.get("blog_comments")

    for key, value in blog_comments.items():
        for key2, value2 in value.items():
            if key2 == title:
                return value2


def calc_posts_statics(calc="all"):

    if calc == "comments" or calc == "all":
        topten_comm_posts = []
        comm_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1 AND state = True ORDER BY comments DESC LIMIT 10",  get_dbkey())

        for post in comm_posts:
            topten_comm_posts.append([post.title, post.comments, post])

        memcache.set("topten_comm_posts", topten_comm_posts)


    if calc == "views" or calc == "all":
        topten_view_posts = []
        view_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1 AND state = True ORDER BY views DESC LIMIT 10",  get_dbkey())

        for post in view_posts:
            topten_view_posts.append([post.title, post.views, post])

        memcache.set("topten_view_posts", topten_view_posts)

    if calc == "admin":
        topten_comm_posts = []
        comm_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1 ORDER BY comments DESC LIMIT 10",  get_dbkey())

        for post in comm_posts:
            topten_comm_posts.append([post.title, post.comments, post])

        memcache.set("topten_comm_posts", topten_comm_posts)


        topten_view_posts = []
        view_posts = db.GqlQuery("SELECT * FROM Blog_Posts WHERE ANCESTOR IS :1 ORDER BY views DESC LIMIT 10",  get_dbkey())

        for post in view_posts:
            topten_view_posts.append([post.title, post.views, post])

        memcache.set("topten_view_posts", topten_view_posts)

        disabled_posts = []
        disabled = db.GqlQuery("SELECT * FROM Blog_Posts WHERE state = False AND ANCESTOR IS :1 ORDER BY comments DESC",  get_dbkey())

        for post in disabled:
            disabled_posts.append([post.title, post.views, post])

        memcache.set("disabled_posts", disabled_posts)


    # for key, value in blog_posts.items():
    #     logging.error("Error %s / %s " % (key, value))

    # for post_id, post in blog_posts.items():

    #     if calc == "comments" or calc == "all":
    #         for x in range(0, len(topten_comm_posts)):
    #             if post.comments >= topten_comm_posts[x][1]:
    #                 topten_comm_posts.pop()
    #                 topten_comm_posts.insert(x, [post.title, post.comments, post])
    #                 break

    #         memcache.set("topten_comm_posts", topten_comm_posts)

    #     if calc == "views" or calc == "all":
    #         for x in range(0, len(topten_view_posts)):

    #             if post.title == topten_view_posts[x][0]:
    #                 if post.views > topten_view_posts[x][1]:
    #                     topten_view_posts[x][1] = post.views
    #                     topten_view_posts[x][2] = post
    #                     break

    #             elif post.views > topten_view_posts[x][1]:
    #                 if len(topten_view_posts) > 10:
    #                     topten_view_posts.pop()

    #                 topten_view_posts.insert(x, [post.title, post.views, post])
    #                 break

    #             elif len(topten_view_posts) < 10:
    #                 topten_view_posts.append([post.title, post.views, post])
    #                 break



    #         memcache.set("topten_view_posts", topten_view_posts)


def setDisablePost(title_id):
    posts = memcache.get("blog_posts")
    post = posts[title_id]

    # if post.state :
    #     post.estate = False

    # else:
    #     post.estate = True

    post.state = not post.state

    post.put()

    calc_posts_statics("comments")

    memcache.set("blog_posts", posts)

    return post

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
    def render_post(self, post, title, u = None, comments = None, commentError = ""):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login") # bad cookie
                return

        if not title == "Home" :

            if not post.state and not u.user_type == "admin":
                self.error(404)
                return

            comments = getCommentsbyTitle(title)

            if comments:
                comments = OrderedDict(sorted(comments.items(), reverse=True))

            title = post.title[1:]

            topten_comm_posts = None
            topten_view_posts = None

            page = "post.html"

        else:
            page = "blog.html"
            calc_posts_statics("views")
            topten_comm_posts = memcache.get("topten_comm_posts")
            topten_view_posts = memcache.get("topten_view_posts")

        self.render(page,
                    post  = post,
                    title = title,
                    user  = u,
                    comments = comments,
                    commentError = commentError,
                    topten_comm_posts = topten_comm_posts,
                    topten_view_posts = topten_view_posts,
                    query = "")


    def get(self, title="/"):

        title = title.replace(" ", "_")

        blog_posts = memcache.get("blog_posts")

        if blog_posts is None:
            make_cache()
            blog_posts = memcache.get("blog_posts")

        post = getPostbytitle(title, view = True)

        if title == "/":
            self.render_post(post=None, title="Home")
            return

        elif post:
            self.render_post(post=post, title=title)
            return

        else:
            self.error(404)
            # error = "The post that you looking for does not exist, try again bro or go <a href='/'>Home</a>."
            # self.render("error.html", error=error, user=None)


    def post(self, post_title):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login") # bad cookie
                return

        comment = cgi.escape(self.request.get('comment'), quote= True)

        post = getPostbytitle(post_title)

        if comment:
            c = Comments( parent      = get_dbkey(),
                          user_id     = u.key().id(),
                          user_name   = u.user_name,
                          post_id     = post.key().id(),
                          post_title  = post_title,
                          post_comment= comment,
                          state       = True)
            c.put()

            blog_comments = memcache.get("blog_comments")

            if blog_comments is None:
                make_cache()
                blog_comments = memcache.get("blog_comments")

            if blog_comments is None: # still empty? easy peasy
                # comments { idpost : { post_title : { comment_id : comment_obj }}}             struct
                blog_comments = { str(post.key().id()) : { post_title : { str(c.key().id()) : c }}}
            else:
                # comments[idpost][post_title][idcomment] = obj_comment                         set
                if str(post.key().id()) in blog_comments:
                    blog_comments[str(post.key().id())][post_title][str(c.key().id())] = c
                else:
                    blog_comments[str(post.key().id())] = { post_title : { str(c.key().id()) : c }}

            memcache.set("blog_comments", blog_comments)

            #update post info in the db and later in the cache
            post.comments += 1 #ammount of comments++
            post.put()

            #update user statics
            u.comments += 1
            u.put()

            users = memcache.get("blog_users")
            users[str(u.key().id())] = u
            memcache.set("blog_users", users)

            blog_posts = memcache.get("blog_posts")
            blog_posts[post.key().id()] = post
            memcache.set("blog_posts", blog_posts)

            calc_posts_statics("comments")
            #TODO: make that ajax reload only the part of the comments

            self.render_post(post = post, title = post_title)
            # self.write("wao so much %s so much %s - %s" % (username, comment, post_title))

        else:
            error = "A empty comment ... Jhon travolta is confused. <br>"
            error += '<iframe src="//giphy.com/embed/rCAVWjzASyNlm" width="480" height="240" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/confused-lego-travolta-rCAVWjzASyNlm">via GIPHY</a></p>'
            self.render_post(post = post, title = post_title, commentError = error)


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

            total_activity = len(memcache.get("blog_posts")) + len(memcache.get("blog_comments"))
            #totalposts = 50;

            self.render("profile.html",
                        title=title,
                        user = u,
                        user_profile = user_data,
                        total_activity = total_activity)
        else:
            self.error(500)
            # error = "User does not exist or is currently invalid."
            # self.render("error.html", error=error, user=None)


class NewPost(Handler):
    def render_newpost(self, u = None, title='', topic='', content='', titleError = '', topicError = '', contentError = ''):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login")# bad cookie or user nor logged
                return

        self.render("newpost.html",
                    posts       = None,
                    user        = u,
                    title       = title,
                    topic       = topic,
                    content     = content,
                    titleError  = titleError,
                    topicError  = topicError,
                    contentError= contentError)


    def get(self):
        self.render_newpost()


    def post(self):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login")
                return

        title   = ''
        topic   = ''
        content = ''
        user    = u.user_name

        titleError   = ''
        topicError   = ''
        contentError = ''

        allgood = True

        title   = cgi.escape(self.request.get('title'), quote= True)
        topic   = cgi.escape(self.request.get('topic'), quote= True)
        content = cgi.escape(self.request.get('content'), quote= True)

        if not title:
            titleError = "The Post must have a title! (face palm)"
            allgood = False

        if not topic:
            topicError = "Did you know that a post MUST have a topic?"
            allgood = False

        if not content:
            contentError = "Are you sure that you want to post with no content? LoL"
            allgood = False

        if allgood:
            blog_posts = memcache.get("blog_posts")

            title = "/" + title.replace(" ", "_")

            post = Blog_Posts( parent = get_dbkey(),
                               title    = title,
                               topic    = topic,
                               content  = content,
                               user     = u.user_name,
                               state    = True,
                               comments = 0,
                               views    = -1) # so, wen the user see it, the counter ll'be 0
            post.put()

            # update user statics
            u.posts += 1
            u.put()

            users = memcache.get("blog_users")
            users[str(u.key().id())] = u
            memcache.set("blog_users", users)

            blog_posts[str(post.key().id())] = post
            memcache.set("blog_posts", blog_posts)

            calc_posts_statics()

            self.redirect("/post%s" % title)
            return
        else:
            self.render_newpost(title       = title,
                                topic       = topic,
                                content     = content,
                                titleError  = titleError,
                                topicError  = topicError,
                                contentError= contentError)


class DisableHandler(Handler):
    def get(self, title_id=None):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str and not title_id is None: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login")
                return

            elif not u.user_type == "admin":
                self.redirect("/")
                return

            post = setDisablePost(title_id)

            self.redirect(post.title)
            return

        self.redirect("/")


class PostHandler(Handler):
    def get(self):
        pass


class AdminPanel(Handler):
    def render_panel(self):
        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login")
                return
            elif not u.user_type == "admin":
                self.redirect("/")
                return
        else:
            self.redirect("/login")
            return

        calc_posts_statics("admin")
        topten_comm_posts = memcache.get("topten_comm_posts")
        topten_view_posts = memcache.get("topten_view_posts")
        disabled_posts    = memcache.get("disabled_posts")

        posts = memcache.get("blog_posts")

        topics = {}
        disabled = {}

        for key, p in posts.iteritems():

            if not p.topic in topics:
                topics[p.topic] = 1
            else:
                topics[p.topic] += 1


        self.render("admin_panel.html",
                    posts       = None,
                    user        = u,
                    title       = "Admin Panel",
                    topics      = topics,
                    chart       = True,
                    topten_comm_posts = topten_comm_posts,
                    topten_view_posts = topten_view_posts,
                    disabled_posts = disabled_posts)

    def get(self):
        self.render_panel()


class SearchHandler(Handler):
    def search_posts(self, query):
        if query :
            matched_posts = {}
            posts = memcache.get("blog_posts")

            query = query[1:].lower()

            for key, p in posts.iteritems():
                if p.state and query in p.title.lower() or query in p.topic.lower() or query in p.content.lower():
                    matched_posts[key] = {  "title"     : p.title,
                                            "topic"     : p.topic,
                                            "content"   : p.content,
                                            "user"      : p.user,
                                            "comments"  : p.comments,
                                            "views"     : p.views,
                                            "modified"  : p.modified.strftime("%b %d, %Y") }
            return matched_posts


    def render_search(self, matched_posts, query):

        user_cookie_str = self.request.cookies.get('user_id')

        if user_cookie_str: # if cookie exist
            u = valid_cookie(user_cookie_str)

            if not u:
                self.redirect("/login")
                return
        else:
            self.redirect("/login")
            return


        self.render("search.html",
                    posts       = None,
                    user        = u,
                    title       = "Search: %s" % query[1:],
                    query       = query[1:],
                    matched_posts = matched_posts)


    def get(self, query="/"):

        if query == "/":
            self.redirect("/")
            return

        matched_posts = self.search_posts(query)

        self.render_search(matched_posts=matched_posts, query=query)


    def post(self, query):
        query = cgi.escape( query, quote= True )

        matched_posts = self.search_posts(query)

        response = "null"

        if matched_posts :
            response = json.dumps(matched_posts)

        self.write( response )

class CommentsHandler(Handler):
    def get(self):
        self.redirect("/")

    def post(self, page):
        comments = getCommentsbyTitle( page )
        comments_json = "null"

        if comments:
            comments_json = {}

            for key, c in comments.iteritems():
                comments_json[key] = {  "user"   : c.user_name,
                                        "comment": c.post_comment,
                                        "created": c.created.strftime("%b %d, %Y") }
            comments_json = json.dumps( comments_json )

        self.write( comments_json )


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
NUM_RE = r'((?:[0-9]+/?)*)'

app = webapp2.WSGIApplication([('/',             MainHandler),
                               ('/search'      + PAGE_RE, SearchHandler),
                               ('/login/?',      LoginHandler),
                               ('/logout/?',     LogoutHandler),
                               ('/signup/?',     SignUpHandler),
                               ('/user'        + PAGE_RE, UserPageHandler),
                               ('/adminpanel/?', AdminPanel),
                               ('/post/new/?',   NewPost),
                               ('/post'        + PAGE_RE, MainHandler),
                               ('/disable/'    + NUM_RE, DisableHandler),
                               ('/getcomments' + PAGE_RE, CommentsHandler),
                               (PAGE_RE,         MainHandler),
                                ], debug=True)
