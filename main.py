import os
from email.mime.multipart import MIMEMultipart
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
from google_auth_oauthlib.flow import InstalledAppFlow
from newsapi.newsapi_client import NewsApiClient
from bs4 import BeautifulSoup
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apscheduler.schedulers.background import BackgroundScheduler
from google.cloud import firestore as cloudFirestore
import urllib.request
from datetime import datetime, timedelta
from flask import Flask, json, request

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

# Use a service account
cred = credentials.Certificate('firebaseServiceAccount.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'gray-area-378308.appspot.com'
})

# Get a reference to the Firestore service and Storage
db = firestore.client()
bucket = storage.bucket()


def save_articles_to_firebase(articles):
    # newsapi = NewsApiClient(api_key='7d414cef315845189aebd171e10c1cb2')
    # top_headlines = newsapi.get_top_headlines(language='en', country='us')
    # print(top_headlines)

    for i, article in enumerate(articles):
        doc_ref = db.collection('articles').document()

        # Download the image from a URL
        url = article['urlToImage']
        filename = doc_ref.id + '.jpg'
        urllib.request.urlretrieve(url, filename)

        # Upload the image to Firebase Storage
        blob = bucket.blob(filename)
        blob.cache_control = 'public, max-age=31536000'
        blob.upload_from_filename(filename)

        # Remove the local file from the file system
        os.remove(filename)

        doc_ref.set({
            'title': article['title'],
            'category': article['category'],
            'description': article['description'],
            'date': cloudFirestore.SERVER_TIMESTAMP,
            'pro_title': article['title_a'],
            'pro': article['narration_a'],
            'against_title': article['title_b'],
            'against': article['narration_b'],
        })

        print(f'Document ID: {doc_ref.id}')


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


def generate_image_url(id):
    blob = bucket.blob(f'{id}.jpg')
    expiration = datetime.utcnow() + timedelta(hours=1)
    download_url = blob.generate_signed_url(expiration=expiration)
    return download_url


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
        description.string = article['description'][:300] + "..."

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


api = Flask(__name__)


@api.route('/get_article', methods=['GET'])
def get_article():
    return json.dumps(db.collection('articles').document(request.args.get('article_id')).get().to_dict())


if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 5000))
    #api.run(host='0.0.0.0', port=port)

    # initialize_gmail_api()
    recipients = [doc.id for doc in db.collection('subscribers').list_documents()]
    print(recipients)

    # Testing things
    send_email(recipients, 'Daily newsletter', insert_into_template(db.collection('articles').stream()))
    # template = open('TheGrayArea-Newsletter-Table.html')
    # soup = BeautifulSoup(template.read(), "html.parser")

    # send_email(recipients, 'Daily newsletter', soup)

    # sched = BackgroundScheduler()
    # sched.start()
    # sched.add_job(hello_world, 'interval', seconds=15, args=['hello'])
    # input("Press enter to exit.")
    # sched.shutdown()
