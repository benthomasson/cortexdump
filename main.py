#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
import os
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from models import Dump, Ganglion

def write_template(handler,templateFile,template_values):
    path = os.path.join(os.path.dirname(__file__), templateFile)
    handler.response.out.write(template.render(path, template_values))

class MainHandler(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    ganglion = None
    dumps = Dump.all().filter('user =',user)
    ganglions = Ganglion.all().filter('user =',user)
    someGanglions = ganglions.count() > 0
    write_template(self,'template/index.html',  { 'dumps': dumps,
                                                  'ganglion': ganglion,
                                                  'ganglions': ganglions,
                                                    'someGanglions':
                                                    someGanglions,
                                                    'user': user, })


class GanglionHandler(webapp.RequestHandler):

    def get(self,key):
        user = users.get_current_user()
        ganglion = Ganglion().get(key)
        dumps = Dump.all().filter('user =',user).filter('ganglion =', ganglion)
        ganglions = Ganglion.all().filter('user =',user)
        someGanglions = ganglions.count() > 0
        write_template(self,'template/index.html',  { 'dumps': dumps,
                                                      'ganglion': ganglion,
                                                  'ganglions': ganglions,
                                                    'someGanglions':
                                                    someGanglions,
                                                    'user': user, })

    def post(self):
        user = users.get_current_user()
        key = self.request.get('key')
        if key:
            try:
                ganglion = Ganglion().get(key)
            except Exception:
                self.redirect('/')
                return
            dumps = Dump.all().filter('user =',user).filter('ganglion =', ganglion)
            ganglions = Ganglion.all().filter('user =',user)
            someGanglions = ganglions.count() > 0
            write_template(self,'template/index.html',  { 'dumps': dumps,
                                                      'ganglion': ganglion,
                                                  'ganglions': ganglions,
                                                    'someGanglions':
                                                    someGanglions,
                                                    'user': user, })
        else:
            self.redirect('/')


class GanglionCreator(webapp.RequestHandler):

    def post(self):
        ganglion = Ganglion()
        ganglion.name = 'New'
        ganglion.user = users.get_current_user()
        ganglion.put()
        self.redirect('/ganglion/%s' % ganglion.key())

class Dumper(webapp.RequestHandler):

    def post(self):
        text = self.request.get('dumptext')
        ganglionKey = self.request.get('ganglion')
        user = users.get_current_user()
        ganglion = None
        if text:
            dump = Dump()
            dump.text = text
            dump.user = users.get_current_user()
            if ganglionKey:
                ganglion = Ganglion.get(ganglionKey)
                if ganglion.user == user:
                    dump.ganglion = ganglion
            dump.put()
        dumps = Dump.all().filter('user =',user)
        if ganglion:
            dumps = dumps.filter('ganglion =',ganglion)
        write_template(self,'template/dumps.html',  { 'dumps': dumps,
                                                    'user': user, })


class Deleter(webapp.RequestHandler):

    def post(self):
        key = self.request.get('key')
        if key:
            dump = Dump().get(key)
            if dump and dump.user == users.get_current_user():
                dump.delete()

def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/dump',Dumper),
                                        ('/dump/delete',Deleter),
                                        ('/ganglion/create',GanglionCreator),
                                        ('/ganglion/(.*)',GanglionHandler),
                                        ('/ganglion',GanglionHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
