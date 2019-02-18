
from flask import Flask
from flask import request
from familyapp.bot import Bot, Button, Template

app = Flask(__name__)

count = 0


def handleChannelAdded(parameters):
    print('handleChannelAdded')
    print(parameters)


def handle_message(parameters):
    print('Message')
    print(parameters)
    global count
    count += 1
    bot.send_message(parameters['family_id'],
                     parameters['conversation_id'], 'Planning message '+str(count))


bot = Bot(token='',
          verify_token='', url='', keys_path='static')
bot.handle_channel_added(handleChannelAdded)
bot.handle_message(handle_message)


@app.route("/", methods=['GET', 'POST'])
def hello():
    bot.parse_request(request.get_json(), headers=request.headers)
    return "Hello World!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
