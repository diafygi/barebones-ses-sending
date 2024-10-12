# Python barebones AWS SES email sending utility

This is a small Python 3 function that you can use in your projects to send email using Amazon Web Services (AWS) Simple Email Service (SES).

It has no other dependencies besides python's standard library, so you can copy-paste `barebones_ses_sending.py` into your project and import it, or you can copy-paste the function code directly into your codebase.

I made this as a small helper utility for my personal projects that need to send email via SES.

## Example use

```python
import os
from email.message import EmailMessage
from email.utils import formataddr
from barebones_ses_sending import send_ses_email

AWS_CONF = {
    "aws_region": os.getenv("AWS_REGION"),
    "aws_key_id": os.getenv("AWS_KEY_ID"),
    "aws_secret": os.getenv("AWS_SECRET"),
}

# Example using EmailMessage
msg = EmailMessage()
msg['From'] = formataddr(("Alice", "alice@example.com"))
msg['To'] = ",".join([formataddr(("Builder, Bob", "bob@example.com")), formataddr(("Carol", "carol@example.com"))])
msg['Subject'] = "My Subject"
msg.set_content("Here's some content")
send_ses_email(msg=msg, **AWS_CONF)

# Example using AWS SES API v2 format (https://docs.aws.amazon.com/ses/latest/APIReference-V2/API_SendEmail.html)
payload = {
    "FromEmailAddress": formataddr(("Alice", "alice@example.com")),
    "Destination": {
        "ToAddresses": [formataddr(("Builder, Bob", "bob@example.com")), formataddr(("Carol", "carol@example.com"))],
    },
    "Content": {
        "Simple": {
            "Subject": { "Data": "My Subject" },
            "Body": { "Text": { "Data": "Here's some content" } },
        },
    },
}
send_ses_email(api_payload=payload, **AWS_CONF)
```

## Copyright

Released under the MIT License.
