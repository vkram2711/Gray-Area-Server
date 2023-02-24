from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import InstalledAppFlow
from bs4 import BeautifulSoup
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore as cloudFirestore

from firebase_utils import generate_image_url

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']


def initialize_gmail_api():
    # Define the scopes that your application needs to access the Gmail API

    # Load the client ID and client secret from the JSON file
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', scopes=SCOPES)

    # Start the OAuth 2.0 authorization flow
    credentials = flow.run_local_server(port=0)

    # Print the refresh token
    print('Refresh token:', credentials.refresh_token)

    # Save the credentials to a JSON file for future use
    with open('credentials.json', 'w') as f:
        f.write(credentials.to_json())


def insert_into_template(articles):
    template = open('TheGrayArea-Newsletter-Table.html')
    soup = BeautifulSoup(template.read(), "html.parser")

    title_and_category = soup.find('tr', attrs={'class': 'titleAndCategory'})
    picture_row = soup.find('tr', attrs={'class': 'pictureRow'})
    description_row = soup.find('tr', attrs={'class': 'descriptionRow'})
    pro_and_against = soup.find('tr', attrs={'class': 'proAndAgainst'})

    html_start = str(soup)[:str(soup).find(str(title_and_category))]
    html_end = str(soup)[str(soup).find(str(title_and_category)) + len(str(title_and_category)) + len(str(picture_row)) + len(str(description_row)) + len(str(pro_and_against)):]
    html_start = html_start.replace('\n', '')
    html_end = html_end.replace('\n', '')
    newsletter_content = ""

    for article in articles:
        article_id = article.id
        article = article.to_dict()
        try:
            img = picture_row.img

            img['src'] = generate_image_url(article_id)
            picture_row.img.replace_with(img)
        except:
            pass

        title = title_and_category.h3
        category = title_and_category.find('p', attrs={'class': 'category'})

        title.string = article['title'][:300]
        category.string = article['category']

        description = description_row.p
        description.string = article['description']

        pro_title = pro_and_against.find('p', attrs={'class': 'proTitle'})
        against_title = pro_and_against.find('p', attrs={'class': 'againstTitle'})
        pro = pro_and_against.find('p', attrs={'class': 'pro'})
        against = pro_and_against.find('p', attrs={'class': 'against'})

        pro_title.string = article["pro_title"]
        against_title.string = article["against_title"]
        pro.string = article["pro"]
        against.string = article["against"]

        #link = article_template.a
        # link['href'] = article['url']
        #link.string = article.id
        #article_template.a.replace_with(link)

        newsletter_content += str(title_and_category).replace('\n', '') + str(picture_row).replace('\n', '') + str(description_row).replace('\n', '') + str(pro_and_against).replace('\n', '')

    email_content = html_start + newsletter_content + html_end
    print(email_content)

    return email_content


def send_email(recipients, subject, content):
    try:
        # Set up OAuth 2.0 credentials
        creds = Credentials.from_authorized_user_file('credentials.json', SCOPES)
        # Create Gmail API client
        service = build('gmail', 'v1', credentials=creds)
        # Create message object
        message = MIMEMultipart("alternative")
        message['from'] = 'Gray Area'
        message['subject'] = subject
        message['Bcc'] = ', '.join(recipients)

        body = MIMEText(content, "html")
        message.attach(body)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        # Send message
        send_message = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(F'sent message to {recipients} Message Id: {send_message["id"]}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None

    return send_message
