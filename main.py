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
from apscheduler.triggers.cron import CronTrigger
from google.cloud.firestore_v1.watch import ChangeType

# Load variables from environment file
load_dotenv()

#mail_utils.initialize_gmail_api()
mail_utils.refresh_gmail()

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

def generate_newsletter_and_send():
    news_generator.top_newsletter()
    mail_utils.send_email(firebase_utils.get_subscribers(), 'Daily Newsletter', insert_into_template(firebase_utils.get_newsletter()))


initial_trigger = False


def on_snapshot(doc_snapshot, changes, read_time):
    global initial_trigger
    for doc in changes:
        document = doc.document
        if doc.type == ChangeType.ADDED and initial_trigger:
            print(document.id)
            mail_utils.send_email([document.id], 'Daily Newsletter', insert_into_template(firebase_utils.get_newsletter()))
    initial_trigger = True


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    current_time = dt.datetime.utcnow()
    query_watch = db.collection('subscribers').on_snapshot(on_snapshot)

    sched = BackgroundScheduler(timezone=pytz.utc)
    sched.start()
    trigger = CronTrigger(
        year="*", month="*", day="*", hour="1", minute="0", second="5", timezone=pytz.utc,
    )
    sched.add_job(generate_newsletter_and_send, trigger=trigger)
    api.run(host='0.0.0.0', port=port)
    sched.shutdown()
