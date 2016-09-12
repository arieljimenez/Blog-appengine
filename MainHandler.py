import time

from Handler import Handler

from collections import OrderedDict

from google.appengine.api import memcache

class MainHandler(Handler):
    def render_post(self, post, title, u = None, comments = None, commentError = "", time_ago = ""):

        u = self.validate_user()

        if not title == "Home" :

            if not post.state:
                if not u or not u.user_type == "admin":
                    self.error(404)
                    return

            comments = self.getCommentsbyTitle(title)

            if comments:
                comments = OrderedDict(sorted(comments.items(), reverse=True))

            title = title.replace("_", " ")[1:]

            topten_comm_posts = None
            topten_view_posts = None

            page = "post.html"

            modified_seg = time.mktime(post.modified.timetuple() )

            seconds_ago = time.time() - modified_seg

            if seconds_ago // (60*60*24*30) >= 1: # total of seconds of a month 60 * 60 * 24 * 30
                time_ago = "%.0f months " % (seconds_ago // (60*60*24*30))

            if (seconds_ago % (60*60*24*30)) // (60*60*24) >= 1: # total of seconds of a day  60 * 60 * 24
                time_ago += "%.0f days " % ((seconds_ago % (60*60*24*30)) // (60*60*24))

            if (seconds_ago % (60*60*24)) // 3600 >= 1: # total of seconds of a hour  60 * 60 * 24
                time_ago += "%.0f hours " % ((seconds_ago % (60*60*24)) // 3600)

            if time_ago == "" :
                time_ago = "%.0f mins" % (seconds_ago // 60)

            #time_ago = "%s months, %s days %s hours" % (time_ago // (60 * 60 * 24 * 30), time_ago // (60 * 60 * 24), time_ago // (60 * 60) )
            #now = time.time() - time.mktime(post.modified.timetuple() ) + post.modified.microsecond
            #t= timedelta( time.time(), (time.mktime(post.modified.timetuple() ) + post.modified.microsecond))

        else:
            page = "blog.html"
            self.calc_posts_statics("views")
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
                    query = "",
                    time_ago = time_ago)


    def get(self, title="/"):

        title = title.replace(" ", "_")

        blog_posts = memcache.get("blog_posts")

        if blog_posts is None:
            self.make_cache()
            blog_posts = memcache.get("blog_posts")

        post = self.getPostbytitle(title, view = True)

        if title == "/":
            self.render_post(post=None, title="Home")
            return

        elif post:
            self.render_post(post=post, title=title)
            return

        else:
            self.error(404)