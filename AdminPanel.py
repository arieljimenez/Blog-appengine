from Handler import Handler

from google.appengine.api import memcache

class AdminPanel(Handler):
    def render_panel(self):
        u = self.validate_user()

        if not u:
            self.redirect("/login")
            return

        elif not u.user_type == "admin":
            self.redirect("/")
            return

        self.calc_posts_statics()

        topten_comm_posts = memcache.get("topten_comm_posts")
        topten_view_posts = memcache.get("topten_view_posts")

        posts = memcache.get("blog_posts")

        topics = {}
        disabled_posts = {}

        for key, p in posts.iteritems():

            if not p.topic in topics:
                topics[p.topic] = 1
            else:
                topics[p.topic] += 1

            if not p.state:
                disabled_posts[p.title] = p

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