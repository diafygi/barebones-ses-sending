"""
This is a small function to send emails via AWS SES using only Python's standard library.
"""
import base64, json, datetime, hashlib, hmac, http.client
from email.utils import formataddr, getaddresses

def send_ses_email(msg=None, api_payload=None, aws_region=None, aws_key_id=None, aws_secret=None):
    """
    Send an email using AWS SES.

    :param msg: The email message you want to send. If None, then api_payload must be provided.
    :type msg: email.message.Message or None

    :param api_payload: A custom AWS SES API v2 SendEmail JSON payload of the email you want to send. If None, then msg must be provided.
    :type api_payload: dict or None

    :param str aws_region: The AWS region your SES config uses (e.g. "us-west-2")
    :param str aws_key_id: Your AWS Key ID that has "ses:SendRawEmail" and "ses:SendEmail" permissions in IAM.
    :param str aws_secret: Your AWS Key ID's secret.

    :return: The response from AWS SES API
    :rtype: http.client.HTTPResponse
    """
    # email sending contents
    addr_list = lambda addr_str: [formataddr((rname, remail)) for rname, remail in getaddresses(addr_str) if remail]
    PAYLOAD = json.dumps(api_payload or {
        "FromEmailAddress": msg['from'],
        "Destination": {
            "ToAddresses": addr_list(msg.get("to", "")),
            "CcAddresses": addr_list(msg.get("cc", "")),
            "BccAddresses": addr_list(msg.get("bcc", "")),
        },
        "ReplyToAddresses": addr_list(msg.get("reply-to", "")),
        "Content": { "Raw": { "Data": base64.b64encode(bytes(msg)).decode() } },
    }).encode()
    NOW = datetime.datetime.utcnow()
    REF = {
        "aws_key_id": aws_key_id,
        "aws_secret": aws_secret,
        "algo": "AWS4-HMAC-SHA256",
        "req_type": "aws4_request",
        "host": "email." + aws_region + ".amazonaws.com",
        "region": aws_region,
        "service": "ses",
        "method": "POST",
        "path": "/v2/email/outbound-emails",
        "query": "",
        "header_names": "content-type;host;x-amz-date",
        "content_type": "application/json",
        "date": NOW.strftime('%Y%m%d'),
        "timestamp": NOW.strftime('%Y%m%dT%H%M%SZ'),
        "payload_hash": hashlib.sha256(PAYLOAD).hexdigest(),
        "request_hash": None,
        "signature": None,
    }
    # Create the canonical request
    canonical_request = (
        "{method}\n"
        "{path}\n"
        "{query}\n"
        "content-type:{content_type}\n"
        "host:{host}\n"
        "x-amz-date:{timestamp}\n"
        "\n"
        "{header_names}\n"
        "{payload_hash}"
    ).format(**REF).encode()
    REF['request_hash'] = hashlib.sha256(canonical_request).hexdigest()
    # Create the signature
    sig_payload = (
        "{algo}\n"
        "{timestamp}\n"
        "{date}/{region}/{service}/{req_type}\n"
        "{request_hash}"
    ).format(**REF).encode()
    kSecret = "AWS4{aws_secret}".format(**REF).encode()
    kDate = hmac.new(kSecret, REF['date'].encode(), hashlib.sha256).digest()
    kRegion = hmac.new(kDate, REF['region'].encode(), hashlib.sha256).digest()
    kService = hmac.new(kRegion, REF['service'].encode(), hashlib.sha256).digest()
    kReqType = hmac.new(kService, REF['req_type'].encode(), hashlib.sha256).digest()
    REF['signature'] = hmac.new(kReqType, sig_payload, hashlib.sha256).hexdigest()
    # Create the authorization header
    authorization_header = (
        "{algo} "
        "Credential={aws_key_id}/{date}/{region}/{service}/{req_type}, "
        "SignedHeaders={header_names}, "
        "Signature={signature}"
    ).format(**REF)
    # Make the request
    conn = http.client.HTTPSConnection(REF['host'])
    conn.request(REF['method'], REF['path'], PAYLOAD, {
        "Host": REF['host'],
        "Content-Type": REF['content_type'],
        "X-Amz-Date": REF['timestamp'],
        "Authorization": authorization_header,
    })
    resp = conn.getresponse()
    return resp
