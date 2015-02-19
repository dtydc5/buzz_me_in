import os
import datetime
import urllib

from google.appengine.ext import ndb
from google.appengine.api import memcache
import webapp2
import jinja2
import yaml

from twilio import twiml
from twilio.util import RequestValidator


OPEN_TIME = 5  # minutes
ACCOUNTS_KEY = ndb.Key("AllAccounts", "AllAccounts")


class Account(ndb.Model):
    name = ndb.StringProperty()
    phone = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def get_by_phone(cls, phone):
        aq = cls.query(ancestor=ACCOUNTS_KEY).filter(cls.phone == phone)
        return aq.get()


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
    
def expandTemplate(fileName, values):
    template = JINJA_ENVIRONMENT.get_template(fileName)
    return template.render(values)


with open("credentials.yaml") as f:
    CREDENTIALS = yaml.safe_load(f)
def isFromTwilio(localUrl, request):
    signature = request.headers["X-Twilio-Signature"]
    validator = RequestValidator(CREDENTIALS["twilio_auth_token"])
    return validator.validate(CREDENTIALS["twilio_base_url"] + localUrl, request.params, signature)


class MainPage(webapp2.RequestHandler):
    def get(self):
        aq = Account.query(ancestor=ACCOUNTS_KEY)
        accounts = aq.fetch()
        
        self.response.write(expandTemplate("main_page.html", {
            "accounts": accounts,
            "duplicate": self.request.get("duplicate"),
        }))

class AddAccount(webapp2.RequestHandler):
    def post(self):
        phone = self.request.get("phone")
        
        if Account.get_by_phone(phone) is not None:
            self.redirect("/?duplicate=" + urllib.quote_plus(phone))
            return
        
        a = Account(parent=ACCOUNTS_KEY)
        a.name = self.request.get("name")
        a.phone = phone
        a.put()
        
        self.redirect("/")

class DeleteAccount(webapp2.RequestHandler):
    def get(self):
        accountKey = ndb.Key(urlsafe=self.request.get("account"))
        accountKey.delete()
        
        self.redirect("/")

class ReceiveCall(webapp2.RequestHandler):
    def post(self):
        memcache.set("call_request", value=str(self.request))
        memcache.set("call_response", value="-1")

        if not isFromTwilio("call", self.request):
            return

        r = twiml.Response()
        r.play(digits="9"*3)
        r.sms("F: %s, CS: %s" % (self.request.get("From"), self.request.get("CallStatus")))
    
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.write(str(r))

        memcache.set("call_response", value=str(self.response))

class ReceiveSMS(webapp2.RequestHandler):
    def post(self):
        memcache.set("sms_request", value=str(self.request))
        memcache.set("sms_response", value="-1")
        
        if not isFromTwilio("sms", self.request):
            return
        
        # does user exist?
        account = Account.get_by_phone(self.request.get("From"))
        if account is None:
            return
            
        account.date = datetime.datetime.utcnow() + datetime.timedelta(minutes=OPEN_TIME);
        account.put()

        r = twiml.Response()
        r.message("Door unlocked for %d minutes" % OPEN_TIME)
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.write(str(r))

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
    ('/', MainPage),
    ('/add', AddAccount),
    ('/delete', DeleteAccount),
    
    ('/call', ReceiveCall),
    ('/sms', ReceiveSMS),
    ('/debug', DisplayDebugInfo),
], debug=True)
 