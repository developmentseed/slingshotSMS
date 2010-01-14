#!/usr/bin/env python
#
# (c) 2009 Kasper Souren
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affro GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
drupal_services is a module to call Drupal Services.

Check /admin/build/services/settings on your Drupal install.

DrupalServices can be passed a configuration dict.  Based on that it
will instantiate the proper class.  Using Drupal Services with keys
but without a session is currently not supported.
"""


import xmlrpclib, time, random, string, hmac, hashlib, pprint

class BasicServices(xmlrpclib.Server):
    """Drupal Services without keys or sessions, not very secure."""
    def __init__(self, url):
        xmlrpclib.Server.__init__(self, url)
        self.connection = self.system.connect()
        # self.sessid = self.connection['sessid']

    def call(self, method_name, *args):
        print self._build_eval_list(method_name, args)
        return getattr(self, method_name)(*self._build_eval_list(method_name, args))
                           
    def _build_eval_list(self, method_name, args):
        # method_name is used in ServicesSessidKey
        return args

    def __eval(self, to_eval):
        print to_eval
        try:
            return eval(to_eval)
        except xmlrpclib.Fault, err:
            print "Oh oh. An xmlrpc fault occurred."
            print "Fault code: %d" % err.faultCode
            print "Fault string: %s" % err.faultString



class ServicesSessid(BasicServices):
    """Drupal Services with sessid."""
    def __init__(self, url, username, password):
        BasicServices.__init__(self, url)
        self.session = self.user.login(self.sessid, username, password)

    def _build_eval_list(self, args):
        return ([self.sessid] + 
                map(None, args)) # Python refuses to concatenate list and tuple
    


class ServicesSessidKey(ServicesSessid):
    """Drupal Services with sessid and keys."""
    def __init__(self, url, username, password, domain, key):
        BasicServices.__init__(self, url)
        self.domain = domain
        self.key = key
        self.session = self.call('user.login', username, password)
        self.sessid = self.session['sessid']

    def _build_eval_list(self, method_name, args):
        hash, timestamp, nonce = self._token(method_name)
        return ([hash,
                 self.domain, timestamp,
                 nonce, self.sessid] +
                map(None, args))

    def _token(self, api_function):
        timestamp = str(int(time.mktime(time.localtime())))
        nonce = "".join(random.sample(string.letters+string.digits, 10))
        return (hmac.new(self.key, "%s;%s;%s;%s" % 
                         (timestamp, self.domain, nonce, api_function), 
                         hashlib.sha256).hexdigest(),
                timestamp,
                nonce)


class ServicesKey(BasicServices):
    """Drupal Services with keys."""
    def __init__(self, url, domain, key):
        BasicServices.__init__(self, url)
        self.domain = domain
        self.key = key

    def _build_eval_list(self, method_name, args):
        hash, timestamp, nonce = self._token(method_name)
        return ([hash,
                 self.domain, 
                 timestamp,
                 nonce] +
                map(None, args))

    def _token(self, api_function):
        timestamp = str(int(time.mktime(time.localtime())))
        nonce = "".join(random.sample(string.letters+string.digits, 10))
        return (hmac.new(self.key, "%s;%s;%s;%s" % 
                         (timestamp, self.domain, nonce, api_function), 
                         hashlib.sha256).hexdigest(),
                timestamp,
                nonce)
