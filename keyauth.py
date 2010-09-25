# vim: ai ts=4 sts=4 et sw=4

import hmac, random, time, hashlib, urllib2, urllib

def keyauth_random():
    " Provide a random, time dependent string "
    hash = hashlib.md5()
    hash.update(str(random.random()))
    return hash.hexdigest()

# Sign a message.
#
# @param $public_key
#   The public key identifying a private key.
# @param $message
#   A string that is the message to hash.
#
# @return
#   An array with the following values:
#   0 - A random unique nonce.
#   1 - The timestamp denoting the validity of the nonce.
#   2 - The hash of message, nonce and timestamp.
def keyauth_sign(private_key, message):
    nonce = keyauth_random()
    timestamp = str(int(time.time()))
    hash = hmac.new(private_key, 
            message + nonce + timestamp, hashlib.sha1)
    return {
            'nonce': nonce, 
            'timestamp': timestamp, 
            'hash': hash.hexdigest()}

def keyauth_post(url, public_key, private_key, message):
    message_encoded = keyauth_sign(private_key, message)
    message_encoded['message'] = message
    message_encoded['public_key'] = public_key
    request = urllib2.Request(url=url, data=urllib.urlencode(message_encoded))
    f = urllib2.urlopen(request)
    return f.read()


# Verify a message.
#
# def keyauth_verify(public_key, message, nonce, timestamp, hash):
#     if (private_key = keyauth_key(public_key)):
#         if (_keyauth_verify_nonce(public_key, nonce, timestamp)):
#             return hash == hmac.new(private_key, message + nonce + timestamp, sha1)
