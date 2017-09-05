import requests 


class APIException(Exception):
    def __init__(self, message, status_code):
        super(Exception, self).__init__(message)
        self.status_code = status_code


class Bot(object):

    def __init__(self, token, verify_token, **kwargs):
        self._handlers = {}
        self.token = token
        self.verify_token = verify_token
        self.url = kwargs.get('url', 'https://api.familyapp.io/')

    def _request(self, suffix_url, data):
        headers = {'User-Agent': 'familyapp.py/0.0.4', 'Authorization': self.token}
        r = requests.post(self.url + suffix_url, json=data, headers=headers)
        if r.status_code in [200, 201]:
            return r.json()

        raise APIException(r.text, status_code=r.status_code)
        
    def send_message(self, family_id, conversation_id, message, **kwargs):
        quick_replies = kwargs.get('quick_replies', [])
        audio_remote_url = kwargs.get('audio_remote_url', '')

        """send textual message"""
        return self._request(
            'bot_api/v1/families/%d/conversations/%d/messages' % (family_id, conversation_id),
            data={
                'content': message,
                'quick_replies_attributes': quick_replies,
                'audio_remote_url': audio_remote_url,
                }
            )

    def handle_message(self, callback):
        """register message_created even handler"""
        self._handlers['message_created'] = callback

    def parse_request(self, json_payload, headers=None):
        """parse incoming requests"""
        if not headers:
            headers = {}
        verify_token = headers.get('Authorization', None)
        event = json_payload.get('event_key', None)

        if verify_token != self.verify_token:
            raise Exception("Invalid verify_token")

        if not event in self._handlers:
            raise Exception("You have to define @familyapp.parse_request")

        del json_payload['event_key']
        self._handlers[event](json_payload)
