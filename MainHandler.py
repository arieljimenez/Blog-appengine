from Handler import Handler

from collections import OrderedDict

from google.appengine.api import memcache

class MainHandler(Handler):
    def render_post(self, post, title, u = None, comments = None, commentError = ""):

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
                    query = "")


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