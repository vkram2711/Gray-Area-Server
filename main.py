import datetime as dt
import os

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, json, request

import firebase_utils
import mail_utils
import news_generator
from firebase_utils import get_newsletter, db
from mail_utils import insert_into_template, send_email

# Load variables from environment file
load_dotenv()

# initialize_gmail_api()

api = Flask(__name__)


@api.route('/get_article', methods=['GET'])
def get_article():
    return json.dumps(db.collection('articles').document(request.args.get('article_id')).get().to_dict())


@api.route('/subscribe', methods=['POST'])
def subscribe():
    email = [request.args.get('email')]
    db.collection('users').document().set(email)
    send_email(email, 'Daily newsletter', insert_into_template(get_newsletter()))
    return json.dumps({"status": "ok"})


@api.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    db.collection('users').document(request.args.get('email')).delete()
    return json.dumps({"status": "ok"})


# @api.route('/get_newsletter', methods=['GET'])
# def get_newsletter():
#    return json.dumps(firebase_utils.get_newsletter())

def generate_newsletter_and_send():
    news_generator.top_newsletter()
    mail_utils.send_email(firebase_utils.get_subscribers(), 'Daily Newsletter', insert_into_template(firebase_utils.get_newsletter()))


if __name__ == '__main__':
    current_time = dt.datetime.utcnow()

    # Create a query to listen for changes on the "my_collection" collection
    # query = db.collection('subscribers')

    # Listen for realtime updates on the query
    # query_watch = query.on_snapshot(on_snapshot)

    # send_email(['leoliuc0519@gmail.com'], 'Daily Newsletter', insert_into_template(get_newsletter()))
    sched = BackgroundScheduler(timezone=pytz.utc)
    sched.start()
    sched.add_job(generate_newsletter_and_send, hour=1)
    port = int(os.environ.get('PORT', 5000))
    api.run(host='0.0.0.0', port=port)

    sched.shutdown()
