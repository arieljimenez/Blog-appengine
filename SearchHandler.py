import cgi
import json

from Handler import Handler

from google.appengine.api import memcache

class SearchHandler(Handler):
    def search_posts(self, query):
        if query :
            matched_posts = {}
            posts = memcache.get("blog_posts")

            query = query[1:].lower().replace("_", " ")

            for key, p in posts.iteritems():
                if p.state and query in p.title.lower() or query in p.topic.lower() or query in p.content.lower() or query in p.user.lower():
                    matched_posts[key] = {  "title"     : p.title,
                                            "topic"     : p.topic,
                                            "content"   : p.content,
                                            "user"      : p.user,
                                            "comments"  : p.comments,
                                            "views"     : p.views,
                                            "modified"  : p.modified.strftime("%b %d, %Y") }
            return matched_posts


    def render_search(self, matched_posts, query):
        u = self.validate_user()

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

        self.write(response)
