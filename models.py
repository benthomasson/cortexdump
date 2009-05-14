from google.appengine.ext import db

class Cortex(db.Model):
    user = db.UserProperty()
    viewMode = db.StringProperty(default="plain")

class Ganglion(db.Model):
    name = db.StringProperty()
    user = db.UserProperty()

class Dump(db.Model):
    text = db.StringProperty()
    user = db.UserProperty()
    order = db.IntegerProperty(default=1001)
    ganglion = db.ReferenceProperty(Ganglion)


