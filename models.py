from google.appengine.ext import db
import re

class Ganglion(db.Model):
    name = db.StringProperty()
    user = db.UserProperty()

class Cortex(db.Model):
    user = db.UserProperty()
    viewMode = db.StringProperty(default="mark")
    default = db.ReferenceProperty(Ganglion)
    showChecked = db.BooleanProperty(default=True)

class Dump(db.Model):
    text = db.StringProperty()
    html = db.TextProperty()
    user = db.UserProperty()
    order = db.IntegerProperty(default=0)
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
        text = re.sub(r'^(/([\S]+))',self.findGanglionLink,text)
        text = re.sub(r'(\s/([\S]+))',self.findGanglionLink,text)
        text = re.sub(r'^!!!(.*)$',r'<h1>\1</h1>',text)
        text = re.sub(r'^!!(.*)$',r'<h2>\1</h2>',text)
        text = re.sub(r'^!(.*)$',r'<h3>\1</h3>',text)
        self.html = text
        self.put()

    def findGanglionLink(self,match):
        name = match.group(2)
        ganglion = Ganglion.all().filter('user =', self.user).filter('name =', name)
        ganglion = ganglion.fetch(1)
        if ganglion:
            ganglion = ganglion[0]
            if ganglion:
                return '<a href="/ganglion/name/%s">%s</a>' % (name,match.group(1))
        return match.group(0)




