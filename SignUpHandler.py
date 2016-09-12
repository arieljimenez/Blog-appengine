import cgi

from Handler import Handler

class SignUpHandler(Handler):
    def render_signup(self, user="", email="", userError="", passError="", verifyError="", mailError="", next_url=""):
        if next_url == "/signup":
            next_url = "/"

        self.render("signup.html",
                    user = user,
                    email = email,
                    userError = userError,
                    passError = passError,
                    verifyError = verifyError,
                    mailError = mailError,
                    next_url=next_url)

    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.render_signup(next_url=next_url)

    def post(self):
        userE   = ''
        passE   = ''
        verifyE = ''
        mailE   = ''

        user  = cgi.escape(self.request.get('username'), quote= True)
        passw = cgi.escape(self.request.get('password'), quote= True)
        verify= cgi.escape(self.request.get('verify'), quote= True)
        email = cgi.escape(self.request.get('email'), quote= True)

        if not self.valid_username(user):
            userE = "Not a valid username"

        if not self.valid_user_pass(passw):
            passE = "Not a valid pass"

        if not self.verify_pass(passw, verify):
            verifyE = "The Passwords dont match!"

        if not self.valid_mail(email):
            mailE = "Not a valid email"

        if len(email) > 0:
            if self.valid_username(user) and self.valid_user_pass(passw) and self.verify_pass(passw, verify) and self.valid_mail(email):
                pass_hash = self.hash_str(passw)
                user_data = self.get_user_by_name(user)

                if user_data: #user exist?
                    userE = "That user already exists."
                    self.render_signup(user, email, userE, passE, verifyE)
                else:
                    #nope.. so, a new user :D
                    u = self.insert_new_user(user_name = user, user_pass = pass_hash, user_mail = email)
                    new_cookie = str("%s|%s" % (u.key().id(), u.user_pass))

                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % new_cookie)

                    self.redirect('/user/%s' % u.user_name)
            else:
                self.render_signup(user, email, userE, passE, verifyE, mailE)

        else: # without mail
            if self.valid_username(user) and self.valid_user_pass(passw) and self.verify_pass(passw, verify):

                pass_hash = self.hash_str(passw)
                user_data = self.get_user_by_name(user)

                if user_data: #user exist?
                    userE = "That user already exists."
                    self.render_signup(user, email, userE, passE, verifyE)

                else:
                    #nope.. so, a new user :D
                    u = self.insert_new_user(user_name = user, user_pass = pass_hash)

                    new_cookie = str("%s|%s" % (u.key().id(), u.user_pass))

                    self.response.headers['Content-Type'] = 'text/plain'
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % new_cookie)

                    # next_url = str(self.request.get('next_url'))
                    # self.redirect(next_url)
                    self.redirect('/user/%s' % u.user_name)
            else:
                self.render_signup(user, email, userE, passE, verifyE)