import cgi

from Handler import Handler
from Blog_Posts import Blog_Posts
#from Blog_Users import Blog_Users # por si da error en el u.put

from google.appengine.api import memcache

class NewPost(Handler):
    def render_newpost(self, u = None, title='', topic='', content='', titleError = '', topicError = '', contentError = ''):
        u = self.validate_user()

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
        u = self.validate_user()

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

            post = Blog_Posts( parent   = self.get_dbkey(),
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

            self.calc_posts_statics()

            total_activity = memcache.get("total_activity")
            total_activity += 1
            memcache.set("total_activity", total_activity)

            self.redirect("/post%s" % title)
            return
        else:
            self.render_newpost(title       = title,
                                topic       = topic,
                                content     = content,
                                titleError  = titleError,
                                topicError  = topicError,
                                contentError= contentError)
