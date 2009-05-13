from google.appengine.ext import db

class Ganglion(db.Model):
    name = db.StringProperty()
    user = db.UserProperty()

class Dump(db.Model):
    text = db.StringProperty()
    user = db.UserProperty()
    ganglion = db.ReferenceProperty(Ganglion)


