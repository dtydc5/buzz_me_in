import os
from google.appengine.api import memcache
import webapp2
import jinja2

import twiml


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
    
def expandTemplate(fileName, values):
    template = JINJA_ENVIRONMENT.get_template(fileName)
    return template.render(values)


class ReceiveCall(webapp2.RequestHandler):
    def post(self):
        r = twiml.Response()
        r.say("F: %s, CS: %s" % (self.request.get("From"), self.request.get("CallStatus")))
        
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
    ('/call', ReceiveCall),
    ('/sms', ReceiveSMS),
    ('/debug', DisplayDebugInfo),
], debug=True)
 