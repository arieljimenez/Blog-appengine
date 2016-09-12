from google.appengine.ext import db

class Comments(db.Model):
    user_id     = db.IntegerProperty(required = True)
    user_name   = db.StringProperty(required = True)
    post_id     = db.IntegerProperty(required = True)
    post_title  = db.StringProperty(required = True)
    post_comment= db.TextProperty(required = True)
    state       = db.BooleanProperty(required = True)
    created     = db.DateTimeProperty(auto_now_add = True)