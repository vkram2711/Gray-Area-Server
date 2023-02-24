
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
from datetime import datetime, timedelta
import datetime as dt
from google.cloud import firestore as cloud_firestore
import urllib.request
import os

# Use a service account
cred = credentials.Certificate('firebaseServiceAccount.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'gray-area-378308.appspot.com'
})


# Get a reference to the Firestore service and Storage
db = firestore.client()
bucket = storage.bucket()


def get_subscribers():
    return [doc.id for doc in db.collection('subscribers').list_documents()]


def get_newsletter():
    today = dt.datetime.utcnow().date()
    # convert to datetime object with midnight as time
    today_start = dt.datetime.combine(today, dt.time.min)

    # query Firestore for documents with timestamp between today_start and today_end
    articles = db.collection('articles').where('date', '>=', today_start).stream()

    articles_list = []
    for article in articles:
        article_dict = article.to_dict()
        print(f"today start {today_start}, article date {article_dict['date']} ")
        articles_list.append(article_dict)

    return articles_list


def generate_image_url(id):
    blob = bucket.blob(f'{id}.jpg')
    expiration = datetime.utcnow() + timedelta(hours=1)
    download_url = blob.generate_signed_url(expiration=expiration)
    return download_url


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
            'date': cloud_firestore.SERVER_TIMESTAMP,
            'pro_title': article['title_a'],
            'pro': article['narration_a'],
            'against_title': article['title_b'],
            'against': article['narration_b'],
        })

        print(f'Document ID: {doc_ref.id}')