from twilio.rest import Client

account = "ACe78c2aecbca3a3117c8f05500841aac0"
token = "7899b0491c270433699db204329bcc3a"
client = Client(account, token)

call = client.calls.create(to="7812493825",
                           from_="6313362896",
                           send_digits = "W1W1W1",
                           url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient")
print(call.sid)
'''
from twilio.rest import TwilioRestClient


# Twilio phone number goes here. Grab one at https://twilio.com/try-twilio
# and use the E.164 format, for example: "+12025551234"
TWILIO_PHONE_NUMBER = "+17812493825"

# list of one or more phone numbers to dial, in "+19732644210" format
DIAL_NUMBERS = ["+16313362896"]

# URL location of TwiML instructions for how to handle the phone call
TWIML_INSTRUCTIONS_URL = \
  "http://static.fullstackpython.com/phone-calls-python.xml"

# replace the placeholder values with your Account SID and Auth Token
# found on the Twilio Console: https://www.twilio.com/console
client = TwilioRestClient("ACe78c2aecbca3a3117c8f05500841aac0", "7899b0491c270433699db204329bcc3a")


def dial_numbers(numbers_list):
    """Dials one or more phone numbers from a Twilio phone number."""
    for number in numbers_list:
        print("Dialing " + number)
        # set the method to "GET" from default POST because Amazon S3 only
        # serves GET requests on files. Typically POST would be used for apps
        client.calls.create(to=number, from_=TWILIO_PHONE_NUMBER,
                            url=TWIML_INSTRUCTIONS_URL, method="GET")


if __name__ == "__main__":
    dial_numbers(DIAL_NUMBERS)
'''