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
import logging
import re

from models import Dump, Ganglion, Cortex


_IPHONE_UA = re.compile(r'Mobile.*Safari')
def is_iphone(request):
    if request.headers.has_key('USER_AGENT'):
        logging.debug( "USER_AGENT %s" % request.headers['USER_AGENT'])
        return _IPHONE_UA.search(request.headers['USER_AGENT']) is not None
    else:
        return False

def write_template(handler,templateFile,template_values):
    logging.debug('is_iphone %s' % is_iphone(handler.request))
    if is_iphone(handler.request):
        path = os.path.join(os.path.dirname(__file__), 'template', 'iphone', templateFile)
    else:
        path = os.path.join(os.path.dirname(__file__), 'template', templateFile)
    handler.response.out.write(template.render(path, template_values))

def getDumpsTemplate(cortex):
    if cortex.viewMode == "mark":
        return 'dumps_mark.html'
    elif cortex.viewMode == "order":
        return 'dumps_order.html'
    elif cortex.viewMode == "edit":
        return 'dumps_edit.html'
    elif cortex.viewMode == "detail":
        return 'dumps_detail.html'
    else:
        return 'dumps_mark.html'


def getCortex(user):
    cortex = Cortex.all().filter('user =', user).fetch(1)
    if not cortex:
        cortex = Cortex()
        cortex.user = user
        cortex.put()
    else:
        cortex = cortex[0]
    return cortex


def getDefault(cortex):
    default = cortex.default
    if not default:
        default = Ganglion()
        default.name = "Cortex Dump"
        default.user = cortex.user
        default.put()
        cortex.default = default
        cortex.put()
    return default

def getDumps(ganglion):
    user = users.get_current_user()
    cortex = getCortex(user)
    if cortex.showChecked:
        logging.debug('Showing checked')
        return ganglion.dump_set.order('order')
    else:
        logging.debug('Hiding checked')
        return ganglion.dump_set.filter('checked =', False).order('order')


class MainHandler(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    cortex = getCortex(user)
    ganglion = getDefault(cortex)
    if not ganglion.checkUser():
        self.error(404)
        return
    dumps = getDumps(ganglion)
    ganglia = Ganglion.all().filter('user =',user).order('name')
    someGanglia = ganglia.count() > 0
    logout = users.create_logout_url('/')
    write_template(self,'index.html',\
        { 'dumps': dumps,
          'showChecked': cortex.showChecked,
          'dumpsTemplate': getDumpsTemplate(cortex),
          'ganglion': ganglion,
          'ganglia': ganglia,
            'someGanglia':
            someGanglia,
            'user': user,
            'logout': logout })


class GanglionHandler(webapp.RequestHandler):

    def get(self,key):
        user = users.get_current_user()
        cortex = getCortex(user)
        ganglion = Ganglion().get(key)
        if not ganglion:
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        dumps = getDumps(ganglion)
        ganglia = Ganglion.all().filter('user =',user).order('name')
        someGanglia = ganglia.count() > 0
        logout = users.create_logout_url('/')
        write_template(self,'index.html', \
            { 'dumps': dumps,
              'ganglion': ganglion,
              'showChecked': cortex.showChecked,
              'dumpsTemplate': getDumpsTemplate(cortex),
              'ganglia': ganglia,
                'someGanglia':
                someGanglia,
                'user': user,
                'logout': logout})

class GanglionHandler2(webapp.RequestHandler):

    def get(self):
        key = self.request.get('key')
        if key:
            self.redirect('/ganglion/%s' % key)
        else:
            self.redirect('/')

    def post(self):
        self.get()


class GanglionChange(webapp.RequestHandler):

    def post(self):
        key = self.request.get('key')
        if not key: 
            self.error(404)
            return
        update_value = self.request.get('update_value')
        if not update_value: 
            self.error(404)
            return
        ganglion = Ganglion.get(key)
        if not ganglion: 
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        ganglion.name = update_value
        ganglion.put()
        self.response.out.write(ganglion.name)

class GanglionDefault(webapp.RequestHandler):

    def post(self):
        key = self.request.get('key')
        if not key: 
            self.error(404)
            return
        ganglion = Ganglion.get(key)
        if not ganglion: 
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        user = users.get_current_user()
        cortex = getCortex(user)
        cortex.default = ganglion
        cortex.put()

class ToggleChecked(webapp.RequestHandler):

    def post(self):
        logging.debug('ToggleChecked ' + repr(self.request.arguments()))
        toggle = self.request.get('toggle')
        user = users.get_current_user()
        cortex = getCortex(user)
        if toggle == "hide":
            cortex.showChecked = False
        elif toggle == "show":
            cortex.showChecked = True
        else:
            self.error(404)
            return
        cortex.put()
        key = self.request.get('key')
        if not key: 
            self.error(404)
            return
        ganglion = Ganglion.get(key)
        if not ganglion: 
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        dumps = getDumps(ganglion)
        write_template(self, getDumpsTemplate(cortex), \
            { 'dumps': dumps,
              'ganglion': ganglion,
              'showChecked': cortex.showChecked,
              'user': user, })


class DumpEdit(webapp.RequestHandler):

    def post(self):
        key = self.request.get('element_id')
        logging.debug('key ' + key)
        if not key: 
            self.error(404)
            return
        update_value = self.request.get('update_value')
        if not update_value: 
            self.error(404)
            return
        dump = Dump.get(key)
        if not dump: 
            self.error(404)
            return
        if not dump.ganglion.checkUser():
            self.error(404)
            return
        dump.processNewText(update_value)
        self.response.out.write(dump.text)


class DumpChecked(webapp.RequestHandler):

    def post(self):
        key = self.request.get('id')
        logging.debug('key ' + key)
        if not key: 
            self.error(404)
            return
        checked = self.request.get('checked')
        logging.debug('checked ' + checked)
        if not checked: 
            self.error(404)
            return
        dump = Dump.get(key)
        if not dump: 
            self.error(404)
            return
        if not dump.ganglion.checkUser():
            self.error(404)
            return
        if checked == "true":
            dump.checked = True 
        else:
            dump.checked = False
        dump.put()
        return

class DumpDetail(webapp.RequestHandler):

    def post(self):
        key = self.request.get('element_id')
        logging.debug('key ' + key)
        if not key: 
            self.error(404)
            return
        update_value = self.request.get('update_value')
        if not update_value: 
            self.error(404)
            return
        dump = Dump.get(key)
        if not dump: 
            self.error(404)
            return
        if not dump.ganglion.checkUser():
            self.error(404)
            return
        dump.detail = update_value
        dump.put()
        self.response.out.write(dump.detail)

class GanglionSorter(webapp.RequestHandler):

    def post(self,key):
        user = users.get_current_user()
        ganglion = Ganglion().get(key)
        if not ganglion:
            logging.error("Cannot find ganglion %s" % key)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        #logging.debug("Sorting %s" % key)
        #logging.debug(repr(self.request.arguments()))
        order = 1
        for dumpKey in self.request.get_all('dump[]'):
            #logging.debug(dumpKey)
            dump = Dump.get(dumpKey)
            if dump:
                #logging.debug("order %s" % order)
                dump.order = order
                dump.put()
            order += 1
        #logging.debug("%s items sorted" % order)
        return

class GanglionByName(webapp.RequestHandler):

    def get(self,name):
        user = users.get_current_user()
        ganglion = Ganglion().all().filter('user =', user).filter('name =', name)
        ganglion = ganglion.fetch(1)
        if not ganglion:
            self.redirect('/')
        else:
            ganglion = ganglion[0]
            if not ganglion.checkUser():
                self.error(404)
                return
            self.redirect('/ganglion/%s' % ganglion.key())


class GanglionCreator(webapp.RequestHandler):

    def post(self):
        ganglion = Ganglion()
        ganglion.name = 'New (Click to change)'
        ganglion.user = users.get_current_user()
        ganglion.put()
        self.redirect('/ganglion/%s' % ganglion.key())

class Dumper(webapp.RequestHandler):

    def post(self):
        text = self.request.get('dumptext')
        ganglionKey = self.request.get('ganglion')
        if ganglionKey:
            ganglion = Ganglion.get(ganglionKey)
        else:
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        user = users.get_current_user()
        cortex = getCortex(user)
        if text:
            dump = Dump()
            dump.user = users.get_current_user()
            if ganglion and ganglion.user == user:
                dump.ganglion = ganglion
            dump.processNewText(text)
        dumps = getDumps(ganglion)
        write_template(self, getDumpsTemplate(cortex), \
            { 'dumps': dumps,
              'showChecked': cortex.showChecked,
              'ganglion': ganglion,
              'user': user, })

    def get(self):
        return self.post()


class Deleter(webapp.RequestHandler):

    def post(self):
        key = self.request.get('key')
        if key:
            dump = Dump().get(key)
            if not dump.ganglion.checkUser():
                self.error(404)
                return
            if dump and dump.user == users.get_current_user():
                dump.delete()

class Migration(webapp.RequestHandler):

    def get(self):
        dumps = Dump.all()
        for dump in dumps.fetch(1000):
            self.response.out.write(dump.text)
            self.response.out.write('<br>')
            dump.order = 1001
            dump.put()

class ViewHandler(webapp.RequestHandler):

    def post(self,view):
        user = users.get_current_user()
        cortex = getCortex(user)
        cortex.viewMode = view
        cortex.put()
        ganglionKey = self.request.get('ganglion')
        ganglion = None
        if not ganglionKey: 
            self.error(404)
            return
        ganglion = Ganglion.get(ganglionKey)
        if not ganglion: 
            self.error(404)
            return
        if not ganglion.checkUser():
            self.error(404)
            return
        dumps = getDumps(ganglion)
        write_template(self, getDumpsTemplate(cortex), \
            { 'dumps': dumps,
              'ganglion': ganglion,
              'user': user, })


def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/dump',Dumper),
                                        ('/dump/edit',DumpEdit),
                                        ('/dump/checked',DumpChecked),
                                        ('/dump/detail',DumpDetail),
                                        ('/dump/delete',Deleter),
                                        ('/ganglion/create',GanglionCreator),
                                        ('/ganglion/change',GanglionChange),
                                        ('/ganglion/toggleChecked',ToggleChecked),
                                        ('/ganglion/default',GanglionDefault),
                                        ('/ganglion/sort/(.*)',GanglionSorter),
                                        ('/ganglion/name/(.*)',GanglionByName),
                                        ('/ganglion/(.*)',GanglionHandler),
                                        ('/ganglion',GanglionHandler2),
                                        ('/view/(.*)',ViewHandler),
                                        #('/migrate',Migration),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
