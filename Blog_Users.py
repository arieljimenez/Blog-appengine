from google.appengine.ext import db

class Blog_Users(db.Model):
    user_name = db.StringProperty(required = True)
    user_pass = db.TextProperty(required = True)
    user_type = db.StringProperty(required = True)
    user_mail = db.StringProperty(required = False)
    siginup   = db.DateTimeProperty(auto_now_add = True)
    comments  = db.IntegerProperty(required = True)
    posts     = db.IntegerProperty(required = True)