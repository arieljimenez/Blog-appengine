import cgi

from Handler import Handler

class LoginHandler(Handler):
    def render_login(self, user="", userError="", passError="", next_url=""):
        self.render("login.html", user = user, userError = userError, passError = passError, next_url=next_url )

    def get(self):
        next_url = self.request.headers.get('referer', '/')
        user_cookie_str = self.request.cookies.get('user_id')

        if next_url == "/login":
            next_url = "/"

        u = self.validate_user()

        if u: # the user is alredy login, redirect him to the main page
            # self.redirect(str(next_url))
            self.redirect("/")
        else:
            self.render_login(next_url=next_url)


    def post(self):
        userE   = ''
        passE   = ''

        user  = cgi.escape(self.request.get('username'), quote= True)
        passw = cgi.escape(self.request.get('password'), quote= True)

        next_url = self.request.get('next_url')

        if not self.valid_username(user):
            userE = "Not a valid username"

        if not self.valid_user_pass(passw):
            passE = "Not a valid pass"

        if self.valid_username(user) and self.valid_user_pass(passw):
            pass_hash = self.hash_str(passw)
            user_data = self.get_user_by_name(user)

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