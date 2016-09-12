from Handler import Handler

class DisableHandler(Handler):
    def get(self, title_id=None):
        u = self.validate_user()

        if not u:
            self.redirect("/login")
            return

        if not u.user_type == "admin":
            self.redirect("/")
            return

        post = self.setDisablePost(title_id)

        self.redirect(post.title)
        return

