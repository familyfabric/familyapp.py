
from flask import Flask
from flask import request
from familyapp.bot import Bot, Button, Template

app = Flask(__name__)


def handleChannelAdded(parameters):
    print(parameters)


def handle_message(parameters):
    print('Message')
    print(parameters)
    bot.send_message(parameters['family_id'],
                     parameters['conversation_id'], 'lame',)


bot = Bot(token="1630036277D45C5E12C8E17915141B25C603240211E148F3C79AD3415238FA35",
          verify_token="F45D2F889667CCD3E91E4EC7658934B3DDB782DFD9FD62A59DBE39B5DA321ABF", url='https://api.staging.familyapp.com/')
bot.handle_channel_added(handleChannelAdded)
bot.handle_message(handle_message)


@app.route("/", methods=['GET', 'POST'])
def hello():
    bot.parse_request(request.get_json(), headers=request.headers)
    return "Hello World!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
