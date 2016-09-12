from Handler import Handler

from google.appengine.api import memcache

class UserPageHandler(Handler):
    def get(self, user):
        user_name = None
        u = self.validate_user()

        user_data = self.get_user_by_name(user[1:])

        if user_data:
            title = "%s is profile " % user_data.user_name

            total_activity = memcache.get("total_activity")

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