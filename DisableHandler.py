import cgi
import json
import logging

from Handler import Handler

from google.appengine.api import memcache

class DisableHandler(Handler):
    def get(self):
        u = self.validate_user()

        if not u:
            self.redirect("/login")
            return

        if not u.user_type == "admin":
            self.redirect("/")
            return

        post_id = cgi.escape(self.request.get('post_id'))

        posts = self.swap_post_state(post_id)

        tt_comments = memcache.get("topten_comm_posts_json")
        tt_views    = memcache.get("topten_view_posts_json")
        disabled_p  = memcache.get("disabled_posts_json")

        json_file = {"tt_comments" : tt_comments,
                     "tt_views"    : tt_views,
                     "disabled_p"  : disabled_p}

        json_file = json.dumps( json_file )

        self.write( json_file )


#FIX THIS THIS!
