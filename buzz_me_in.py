import os

from google.appengine.ext import ndb
from google.appengine.api import memcache
import webapp2
import jinja2

import twiml


ACCOUNTS_KEY = ndb.Key("AllAccounts", "AllAccounts")
class Account(ndb.Model):
    name = ndb.StringProperty()
    phone = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
    
def expandTemplate(fileName, values):
    template = JINJA_ENVIRONMENT.get_template(fileName)
    return template.render(values)


class EditAccounts(webapp2.RequestHandler):
    def get(self):
        aq = Account.query(ancestor=ACCOUNTS_KEY)
        accounts = aq.fetch()
        
        self.response.write(expandTemplate("edit_accounts.html", {
            "accounts": accounts,
        }))

class AddAccount(webapp2.RequestHandler):
    def post(self):
        a = Account(parent=ACCOUNTS_KEY)
        a.name = self.request.get("name")
        a.phone = self.request.get("phone")
        a.put()
        
        self.redirect("/")

class DeleteAccount(webapp2.RequestHandler):
    def get(self):
        accountKey = ndb.Key(urlsafe=self.request.get("account"))
        accountKey.delete()
        
        self.redirect("/")

class ReceiveCall(webapp2.RequestHandler):
    def post(self):
        r = twiml.Response()
        r.play(digits="9"*3)
        r.sms("F: %s, CS: %s" % (self.request.get("From"), self.request.get("CallStatus")))
        
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.write(str(r))

        memcache.set("call_request", value=str(self.request))
        memcache.set("call_response", value=str(self.response))

class ReceiveSMS(webapp2.RequestHandler):
    def post(self):
        r = twiml.Response()
        r.message("F: %s, B: %s" % (self.request.get("From"), self.request.get("Body")))
        
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.write(str(r))

        memcache.set("sms_request", value=str(self.request))
        memcache.set("sms_response", value=str(self.response))

class DisplayDebugInfo(webapp2.RequestHandler):
    def get(self):
        self.response.write(expandTemplate("debug.html", dict(
            map(lambda k: (k, memcache.get(k)), [
                "call_request",
                "call_response",
                "sms_request",
                "sms_response"
            ])
        )))


application = webapp2.WSGIApplication([
    ('/', EditAccounts),
    ('/add', AddAccount),
    ('/delete', DeleteAccount),
    
    ('/call', ReceiveCall),
    ('/sms', ReceiveSMS),
    ('/debug', DisplayDebugInfo),
], debug=True)
 