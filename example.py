from familyapp.bot import Bot, Button, Template

if __name__ == "__main__":
    bot = Bot(token="", verify_token="", url='https://api.staging.familyapp.io/')
    r = bot.send_message(35, 296, "test", template=Template(buttons=[
        Button("test", "TEST_BUTTON"),
        Button("test2", "TEST2_BUTTON"),
    ]))
