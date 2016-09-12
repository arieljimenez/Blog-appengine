import cgi
import json

from Handler import Handler
from Comments import Comments

from google.appengine.api import memcache

class CommentsHandler(Handler):
    def get(self):
        action = self.request.get('action')

        if action == "updateComment":
            comment_id = self.request.get('id')
            updatedComment = self.request.get('comment')

            self.update_comment(comment_id=comment_id, updatedComment=updatedComment)
            comments_json = json.dumps({"status": True})
            self.write(comments_json)
            return

        elif action == "getCommentsUser":
            user = self.request.get('user')
            comments = self.get_comments_by_user(user)
            comments = json.dumps( sorted(comments.iteritems()))
            self.write (comments)
            return

        page = self.request.get('page')

        if page:
            page = "/" + page
            comments = self.getCommentsbyTitle(page)
            comments_json = "null"

            if comments:
                comments_json = {}

                for key, c in comments.iteritems():
                    comments_json[c.created.strftime("%y-%m-%d %H:%M:%S.%f")] = {  "user"   : c.user_name,
                    # comments_json[key] = {  "user"   : c.user_name,
                                            "comment": c.post_comment,
                                            "created"   : c.created.strftime("%b %d, %Y"),
                                            "id" : str(c.key().id()),
                                            "time": c.created.strftime("%y-%m-%d %H:%M:%S.%f")}

                comments_json = json.dumps( sorted(comments_json.iteritems()) )
            #logging.error( sorted(comments_json.iteritems()) )

            self.write(comments_json)

        else:
            self.redirect("/")

    def post(self):
        u = self.validate_user()

        post_title = self.request.get('page')
        comment = cgi.escape(self.request.get('comment'), quote= True)

        post = self.getPostbytitle(post_title)

        if comment:
            c = Comments( parent      = self.get_dbkey(),
                          user_id     = u.key().id(),
                          user_name   = u.user_name,
                          post_id     = post.key().id(),
                          post_title  = post_title,
                          post_comment= comment,
                          state       = True)
            c.put()

            blog_comments = memcache.get("blog_comments")

            if blog_comments is None:
                self.make_cache()
                blog_comments = memcache.get("blog_comments")

            if blog_comments is None: # still empty? easy peasy
                blog_comments = { post_title : { str(c.key().id()) : c } }
                #old
                # comments { idpost : { post_title : { comment_id : comment_obj }}}             struct
                #blog_comments = { str(post.key().id()) : { post_title : { str(c.key().id()) : c }}}
            else:
                # comments[idpost][post_title][idcomment] = obj_comment                         set
                if post_title in blog_comments:
                    blog_comments[post_title][str(c.key().id())] = c
                else:
                    blog_comments[post_title] = { str(c.key().id()) : c }

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

            total_activity = memcache.get("total_activity")
            total_activity += 1
            memcache.set("total_activity", total_activity)

            self.calc_posts_statics("comments")
            #self.response.headers = {'Content-Type': 'application/json; charset=utf-8'}
            response = json.dumps({"operation": "success"})
            self.write(response)