import requests


class APIException(Exception):
    def __init__(self, message, status_code=None):
        super(Exception, self).__init__(message)
        self.status_code = status_code


class QuickReplay(object):
    def __init__(self, title, payload=None):
        self.title = title
        self.payload = payload

    def as_dict(self):
        return {'title': self.title, 'payload': self.payload}


class Bot(object):
    def __init__(self, token, verify_token, **kwargs):
        self._handlers = {}
        self.token = token
        self.verify_token = verify_token
        self.url = kwargs.get('url', 'https://api.familyapp.io/')

    def _request(self, method, suffix_url, data):
        if method.lower() not in ['get', 'post', 'patch']:
            raise APIException("Invalid method type, only [get, post, patch] is supported")

        headers = {'User-Agent': 'familyapp.py/0.0.6', 'Authorization': self.token}
        r = getattr(requests, method.lower())(self.url + suffix_url, json=data, headers=headers)
        if r.status_code in [200, 201]:
            return r.json()

        raise APIException(r.text, status_code=r.status_code)

    def send_message(self, family_id, conversation_id, message, quick_replies=None, audio_remote_url=None,
                     photo_base64=None):
        """send message to selected conversation

        :param family_id: ID of selected family (required)
        :type family_id: int
        :param conversation_id: ID of the conversation within the family (required)
        :type conversation_id: int
        :param message: content of the message (optional)
        :type message: str
        :param quick_replies: list of QuickReplay (optional)
        :type quick_replies: list
        :param audio_remote_url: link to remote file location, will be downloaded by the server (optional)
        :type audio_remote_url: str
        :param photo_base64: base64 string of the image
        :type photo_base64: str
        :return: request object
        """
        quick_replies = [] if not quick_replies else map(lambda x: x.as_dict(), quick_replies)

        """send textual message"""
        return self._request(
            'POST',
            'bot_api/v1/families/%d/conversations/%d/messages' % (family_id, conversation_id),
            data={
                'content': message,
                'quick_replies_attributes': quick_replies,
                'audio_remote_url': audio_remote_url,
                'photo': photo_base64,
            }
        )

    def update_family_user(self, family_id, user_id, username=None, phone_number=None, email=None, birthday=None,
                           photo=None, photo_remote_url=None):
        """update family member profile

        :param family_id: ID of selected family (required)
        :type family_id: int
        :param user_id: ID of the family ember (required)
        :type user_id: int
        :param username: username of the user (optional)
        :type username: str
        :param phone_number: phone number of the user (optional)
        :type phone_number: str
        :param email: email of the user (optional)
        :type email: str
        :param birthday: date of birthday, formatted as MM.DD.YYYY (optional)
        :type birthday: datetime
        :param photo: base64 string of the image (optional)
        :type photo: str
        :param photo_remote_url: remote url to the picture, will be downloaded by the server (optional)
        :type photo_remote_url: str
        """
        return self._request(
            'PATCH',
            'bot_api/v1/families/%d/family_users/%d' % (family_id, user_id),
            data={
                'username': username,
                'phone_number': phone_number,
                'email': email,
                'birthday': birthday,
                'photo': photo,
                'photo_remote_url': photo_remote_url,
            }
        )

    def update_channel(self, name=None, photo=None):
        """update family member profile

        :param name: new name of the channel
        :type name: str
        :param photo: base64 string of the image (optional)
        :type photo: str
        """
        return self._request(
            'PATCH',
            'bot_api/v1/channel',
            data={
                'name': name,
                'photo': photo,
            }
        )

    def handle_message(self, callback):
        """triggered when new messages has been sent
        READ MORE: https://familyappbot.docs.apiary.io/#introduction/webhooks/4.-receive-messages
        """
        self._handlers['message_created'] = callback

    def handle_member_joined(self, callback):
        """triggered when new family member joined family
        READ MORE: https://familyappbot.docs.apiary.io/#introduction/webhooks/4.-receive-messages
        """
        self._handlers['joined_to_family'] = callback

    def handle_member_left(self, callback):
        """triggered when user left family
        READ MORE: https://familyappbot.docs.apiary.io/#introduction/webhooks/4.-receive-messages
        """
        self._handlers['left_from_family'] = callback

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
