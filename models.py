from google.appengine.ext import db

class Dump(db.Model):
    text = db.StringProperty()
    user = db.UserProperty()

