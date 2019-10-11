""""
Send emails using SES. SES Credentials must be stored in ~/.aws/credentials.
"""

import boto3
from botocore.exceptions import ClientError

container_template_filename = 'container.html'

def send_digest_email(recipient, topics_contents, posts_contents, summary, subject,
                      manage_emails_url, template, special_contents, favorite_contents, username):
    """ Assemble the contents into a template and send it using SES """

    special_contents = special_contents or ''
    favorite_contents = favorite_contents or ''

    f = file(template, 'rt')
    email_template = f.read()
    f.close()

    f = file(container_template_filename, 'rt')
    container = f.read()
    f.close()

    contents = email_template
    if special_contents or favorite_contents:
        contents = contents.replace('[[CONTAINER]]', container)
    else:
        contents = contents.replace('[[CONTAINER]]', '')      
    contents = contents.replace('[[TOPICS]]', topics_contents)
    contents = contents.replace('[[POSTS]]', posts_contents)
    contents = contents.replace('[[ACTIVITY_SUMMARY]]', summary)
    contents = contents.replace('[[MANAGE_EMAILS_URL]]', manage_emails_url)
    contents = contents.replace('[[SPECIAL_POST]]', special_contents)
    contents = contents.replace('[[FAVORITE_POST]]', favorite_contents)
    contents = contents.replace('[[USERNAME]]', username)

    # This address must be verified with Amazon SES.
    SENDER = "506 Investor Group Digest <noreply@506investorgroup.com>"

    RECIPIENT = recipient

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"

    # The subject line for the email.
    SUBJECT = subject # "506 Investor Group Activity Summary"

    # The email body for recipients with non-HTML email clients.
    # I did not do this as nobody in the group is using text-only emails.
    BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto)."
                 )

    # The HTML body of the email.
    BODY_HTML = contents

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def send_simple_email(recipient, subject, contents, sender="506 Investor Group <noreply@506investorgroup.com>"):
    """ Send a very simple email. Not currently used. """
    SENDER = sender
    RECIPIENT = recipient
    AWS_REGION = "us-west-2"
    SUBJECT = subject
    BODY_TEXT = ("")
    BODY_HTML = contents
    CHARSET = "UTF-8"
    client = boto3.client('ses', region_name=AWS_REGION)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

if __name__ == '__main__':
    send_simple_email('markschmucker@yahoo.com', 'test from ses.py', 'this is a test')
