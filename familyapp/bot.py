import requests
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
import pickle
import base64
import os


class APIException(Exception):
    def __init__(self, message, status_code=None, url=None, data=None,):
        super(Exception, self).__init__(message)
        self.status_code = status_code
        self.url = url
        self.message = message
        self.data = data

    def __str__(self):

        return f'{self.url} {self.status_code} {self.data}'


class QuickReply(object):
    def __init__(self, title, payload=None):
        """Quick Reply

        :param title: text of the button (required)
        :type title: str
        :param payload: string with payload (optional)
        :type payload: str
        """
        self.title = title
        self.payload = payload

    def as_dict(self):
        return {'title': self.title, 'payload': self.payload}


class Button(object):
    def __init__(self, title, payload=None, web_url=None):
        """Button Attributes

        :param title: text of the button (required)
        :type title: str
        :param payload: string with payload (optional)
        :type payload: str
        :param web_url: URL to the page (optional)
        :type web_url: str
        """
        self.title = title
        self.payload = payload
        self.web_url = web_url

    @property
    def type(self):
        return 'postback' if self.payload else ':web_url'

    def as_dict(self):
        return {
            'title': self.title,
            'payload': self.payload,
            'url': self.web_url,
            'button_type': self.type
        }


class Element(object):
    def __init__(self, title, subtitle=None, image=None):
        """Element Attributes

        :param title: text of the element (required)
        :type title: str
        :param subtitle: subtitle of element (optional)
        :type subtitle: str
        :param image: base64 of the image
        :type image: str
        """
        self.title = title
        self.subtitle = subtitle
        self.image = image

    def as_dict(self):
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'image': self.image
        }


class Template(object):
    def __init__(self, buttons=None, elements=None, template_type='buttons'):
        """Builder for template object

        :param buttons: List of ButtonAttributes (optional)
        :type buttons: list
        :param elements: List of ElementAttributes (optional)
        :type elements: list
        :param template_type: Type of template ('buttons' or 'list') (optional)
        :type str
        """
        self.template_type = template_type
        self.buttons = buttons if buttons else []
        self.elements = elements if elements else []

    def as_dict(self):
        buttons = [x.as_dict() for x in self.buttons]
        elements = [x.as_dict() for x in self.elements]
        return {
            'buttons_attributes': buttons,
            'elements_attributes': elements,
            'template_type': self.template_type
        }


class Bot(object):

    def __init__(self, token, verify_token, **kwargs):
        self._handlers = {}
        self.token = token
        self.verify_token = verify_token
        self.url = kwargs.get('url', 'https://api.familyapp.com/')
        self.keys_path = kwargs.get('keys_path', '')
        self._init_data()

    def _init_data(self):
        if not os.path.exists(self.keys_path):
            os.makedirs(self.keys_path)
        self.data = {'rsa_private': None,
                     'rsa_public': None,
                     'rsa_id': None}
        self.conversation_data = {'keys': {}, 'conversations': {}}
        self._load_data()
        self._load_conversation_data()
        if self.data.get('rsa_id', None) is None:
            self._generate_RSA()

    def _load_data(self):
        try:
            with open(os.path.join(self.keys_path, f'rsa_{self.token}.pickle'), 'rb') as handle:
                self.data = pickle.load(handle)
        except(OSError, IOError) as e:
            print(e)
        except(FileNotFoundError):
            pass

    def _save_data(self):
        try:
            with open(os.path.join(self.keys_path, f'rsa_{self.token}.pickle'), 'wb') as handle:
                pickle.dump(self.data, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)
        except(OSError, IOError, FileNotFoundError) as e:
            print(e)

    def _load_conversation_data(self):
        try:
            with open(os.path.join(self.keys_path, f'conversations_{self.token}.pickle'), 'rb') as handle:
                self.conversation_data = pickle.load(handle)
        except(OSError, IOError) as e:
            print(e)
        except(FileNotFoundError):
            pass

    def _save_conversation_data(self):
        try:
            with open(os.path.join(self.keys_path, f'conversations_{self.token}.pickle'), 'wb') as handle:
                pickle.dump(self.conversation_data, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)
        except(OSError, IOError, FileNotFoundError) as e:
            print(e)

    def _generate_RSA(self):
        '''
        Generate an RSA keypair with an exponent of 65537 in PEM format
        param: bits The key length in bits
        Return private key and public key
        '''
        bits = 2048
        new_key = RSA.generate(bits, e=65537)
        public_key = new_key.publickey().exportKey("PEM").decode("utf-8")
        private_key = new_key.exportKey("PEM").decode("utf-8")
        self.data['rsa_public'] = public_key
        self.data['rsa_private'] = private_key
        response = self._register_rsa_key()
        self.data['rsa_id'] = response['id']
        self._save_data()
        return private_key, public_key

    def _register_rsa_key(self):
        return self._request('POST', 'bot_api/v1/rsa_keys',
                             {'key': str(self.data['rsa_public'])})

    def _decrypt_message(self, message):
        # {'family_id': '60ab2c18-a115-464a-91e4-085813fe6394', 'conversation_id': '97e61e6f-8420-475c-916e-cad12dec157d', 'author': {'id': '20ed218b-bb85-4a09-9469-39571c00e6d0', 'username': None}, 'content': 'm0FRLB6eJdPTiyT7bSY6mw==', 'payload': None, 'attachments': [], 'location': None, 'iv': 'fzmwbr5Mhn8UyvFKh5wSsQ==', 'conversation_key_version_id': 'b5c87c8a-cd68-45d5-a4d2-b76678e5a1fd', 'key_version': 1549629588}
        aes_key = self.get_aes_key(message)
        IV = base64.b64decode(message['iv'])
        aes = AES.new(aes_key, AES.MODE_CBC, IV)
        decrypted_message = aes.decrypt(base64.b64decode(message['content']))
        decrypted_message = decrypted_message[:-
                                              ord(decrypted_message[len(decrypted_message)-1:])].decode("utf-8")
        message['is_decrypted'] = True
        message['content'] = decrypted_message
        return message

    def get_aes_key(self, message):
        conversation_key_version_id = message['conversation_key_version_id']
        try:
            return self.conversation_data['keys'][conversation_key_version_id]
        except KeyError:
            pass
        family_id = message['family_id']
        conversation_id = message['conversation_id']
        conversation = self.get_conversation(family_id, conversation_id)
        rsa_id = self.data['rsa_id']

        def filter_conversation_keys(key):
            return key['conversation_key_version_id'] == conversation_key_version_id and key['rsa_key_id'] == rsa_id
        conversation_keys = list(filter(
            filter_conversation_keys, conversation['conversation_keys']))
        rsa_public = RSA.importKey(self.data['rsa_public'])
        rsa_private = RSA.importKey(self.data['rsa_private'])
        encrypted_key = base64.b64decode(conversation_keys[0]['key'])
        cipher = PKCS1_v1_5.new(rsa_private)
        decrypted_key = cipher.decrypt(encrypted_key, b'DECRYPTION FAILED')
        decoded_decrypted_key = base64.b64decode(decrypted_key)
        self.conversation_data['keys'][conversation_key_version_id] = decoded_decrypted_key
        self.conversation_data['conversations'][conversation_id] = {
            'family_id': family_id, 'conversation_key_version_id': conversation_key_version_id}
        self._save_conversation_data()
        return decoded_decrypted_key

    def get_conversation_key_if_exists(self, family_id, conversation_id):
        try:
            conversation_key_version_id = self.conversation_data[
                'conversations'][conversation_id]['conversation_key_version_id']
            return (self.conversation_data['keys'][conversation_key_version_id], conversation_key_version_id)
        except KeyError:
            return None, None

    def _pad(self, s):
        block_size = 16
        return s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)

    def _request(self, method, suffix_url, data=None):
        if method.lower() not in ['get', 'post', 'patch']:
            raise APIException(
                "Invalid method type, only [get, post, patch] is supported"
            )

        headers = {
            'User-Agent': 'familyapp.py/0.0.11',
            'Authorization': self.token
        }
        r = getattr(requests, method.lower())(
            self.url + suffix_url, json=data, headers=headers, verify=False
        )
        if r.status_code in [200, 201]:
            return r.json()
        raise APIException(r.text, status_code=r.status_code,
                           data=data, url=suffix_url)

    def send_message(self, family_id, conversation_id, message, quick_replies=None,
                     template=None, audio_remote_url=None, photo_base64=None):
        """send message to selected conversation

        :param family_id: ID of selected family (required)
        :type family_id: int
        :param conversation_id: ID of the conversation within the family (required)
        :type conversation_id: int
        :param message: content of the message (optional)
        :type message: str
        :param quick_replies: list of QuickReply (optional)
        :type quick_replies: list
        :param template: Template object
        :type Template
        :param audio_remote_url: link to remote file location, will be downloaded by the server (optional)
        :type audio_remote_url: str
        :param photo_base64: base64 string of the image
        :type photo_base64: str
        :return: request object
        """
        quick_replies = [x.as_dict()
                         for x in quick_replies] if quick_replies else []

        data = {
            'content': message,
            'template_attributes': template.as_dict() if template else None,
            'quick_replies_attributes': quick_replies,
            'audio_remote_url': audio_remote_url,
            'photo': photo_base64,
        }

        self.encryptMessage(family_id, conversation_id, data)

        print('Send')
        print(data)
        """send textual message"""
        return self._request(
            'POST',
            f'bot_api/v1/families/{family_id}/conversations/{conversation_id}/messages',
            data=data
        )

    def encryptMessage(self, family_id, conversation_id, data):
        (key, conversation_key_version_id) = self.get_conversation_key_if_exists(
            family_id, conversation_id)
        if key is None:
            return data
        IV = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, IV)
        message = cipher.encrypt(self._pad(data['content']))
        IV_base64 = base64.b64encode(IV)
        message_base64 = base64.b64encode(message)
        data['content'] = message_base64.decode("utf-8")
        data['iv'] = IV_base64.decode("utf-8")
        data['conversation_key_version_id'] = conversation_key_version_id
        return data

    def get_conversation(self, family_id, conversation_id):
        """get conversation data

        {
            "id": 1,
            "channel_id": 10,
            "family_users": [
                {
                    "id": 1,
                    "username": "John",
                    "photo_url": "",
                    "photo_medium_url": "",
                    "email": "support@familyapp.net",
                    "phone_number: "+100000000",
                    "admin": false,
                    "child_account": true
                },
                {
                    "id": 2,
                    "username": "Bob",
                    "photo_url": "",
                    "photo_medium_url": "",
                    "email": "bob@familyapp.net",
                    "phone_number: "+100000002",
                    "admin": true,
                    "child_account": false
                }
            ]
        }

        :param family_id:
        :type family_id: int
        :param conversation_id:
        :type conversation_id: int
        :return:
        """
        return self._request(
            'GET',
            f'bot_api/v1/families/{family_id}/conversations/{conversation_id}'
        )

    def create_conversation(self, family_id, title):
        """create conversation

        :param family_id: ID of selected family (required)
        :type family_id: int
        :param title:
        :type title: str
        """
        return self._request(
            'POST',
            'bot_api/v1/families/%d/conversations' % (family_id),
            data={
                'title': title,
            }
        )

    def update_family_user(self, family_id, user_id, username=None, phone_number=None,
                           email=None, birthday=None, photo=None, photo_remote_url=None):
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

    def create_event(self, family_id, title, description, start_time, end_time):
        """create event in family calendar

        :param family_id: ID of selected family (required)
        :type family_id: int
        :param title: title of event (required)
        :type title: str
        :param description: description of event
        :type description: str
        :param start_time: start date of event, formatted as MM.DD.YYYY (required)
        :type start_time: datetime
        :param end_time: end date of event, formatted as MM.DD.YYYY (required)
        :type end_time: datetime
        :param recurring: formatted with RRULE recurring event format (optional)
        :type recurring: str
        :param family_user_ids
        :type family_user_ids: list
        :return: request object
        """
        return self._request(
            'POST',
            'bot_api/v1/families/%d/events' % (family_id),
            data={
                'title': title,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'recurring': recurring,
                'family_user_ids': family_user_ids
            }
        )

    def update_persistent_menu(self, persistent_menu):
        """update peristant menu

        {
            "persistent_menu": [
                {
                    "locale": "default",
                    "composer_input_disabled": false,
                    "call_to_actions": [
                        {
                            "title": "WP",
                            "type": "web_url",
                            "url": "http://www.wp.pl"
                        },
                        {
                            "title": "Actions",
                            "type": "nested",
                            "call_to_actions": [
                                {
                                    "title": "Quick Replies",
                                    "type": "postback",
                                    "payload": "QUICK"
                                },
                                {
                                    "title": "Template Buttons",
                                    "type": "postback",
                                    "payload": "BUTTONS"
                                },
                                {
                                    "title": "Template List",
                                    "type": "postback",
                                    "payload": "LIST"
                                },
                                {
                                    "title": "Template Carousel",
                                    "type": "postback",
                                    "payload": "CAROUSEL"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        :param persistent_menu:
        :type persistent_menu: json
        """
        return self._request(
            'PATCH',
            'bot_api/v1/bot',
            data={
                'persistent_menu': persistent_menu
            }
        )

    def handle_channel_added(self, callback):
        """triggered when family adds channel
        READ MORE: https://familyappbot.docs.apiary.io/#introduction/webhooks/4.-receive-messages
        """
        self._handlers['add_channel_to_family'] = callback

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
        event = json_payload.get('event_type', None)

        if verify_token != self.verify_token:
            raise Exception("Invalid verify_token")

        if event not in self._handlers:
            raise Exception("Event type ({}) is not handled".format(event))

        if 'event_data' not in json_payload:
            raise Exception("Invalid JSON payload")
        if event == 'message_created':
            decrypted_message = self._decrypt_message(
                json_payload['event_data'])
            self._handlers[event](decrypted_message)
            return
        self._handlers[event](json_payload['event_data'])
