from google.appengine.ext import db
import re

class Cortex(db.Model):
    user = db.UserProperty()
    viewMode = db.StringProperty(default="mark")

class Ganglion(db.Model):
    name = db.StringProperty()
    user = db.UserProperty()

class Dump(db.Model):
    text = db.StringProperty()
    html = db.StringProperty()
    user = db.UserProperty()
    order = db.IntegerProperty(default=1001)
    ganglion = db.ReferenceProperty(Ganglion)
    detail = db.TextProperty()
    checked = db.BooleanProperty(default=False)

    def getHtml(self):
        if self.html:
            return self.html
        else:
            return self.text


    def processNewText(self,text):
        self.text = text
        text = re.sub(r'(http://[\S]+)',r'<a href="\1">\1</a>',text)
        self.html = text
        self.put()
