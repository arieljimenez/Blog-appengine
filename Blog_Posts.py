from google.appengine.ext import db


class Blog_Posts(db.Model):
    title   = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    topic   = db.StringProperty(required = True)
    user    = db.StringProperty(required = True)
    state   = db.BooleanProperty(True)
    modified= db.DateTimeProperty(auto_now_add = True)
    comments= db.IntegerProperty()
    views   = db.IntegerProperty()