# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client

# Replace these with your actual Twilio Account SID and Auth Token
account_sid = "AC621720bc2a93841757a47f8db38cb137"
auth_token = "d52e13f3cdc6c9b12fdfe1b94e55fd92"

client = Client(account_sid, auth_token)

# Sending a media message through WhatsApp
message = client.messages.create(
        media_url=["https://www.ieepuebla.org.mx/prevfiles/normatividad/manualOrganizacionIEE.pdf"],  # URL of the media (PDF)
    from_="whatsapp:+14155238886",  # Your Twilio Sandbox number
    to="whatsapp:+5213112655916"  # Recipient's WhatsApp number
)

# Print message SID to confirm it was sent
print(message.sid)

