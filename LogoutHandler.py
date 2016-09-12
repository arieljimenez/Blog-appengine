import webapp2

class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        next_url = self.request.headers.get('referer', '/')
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        #self.redirect(str(next_url))
        self.redirect("/")