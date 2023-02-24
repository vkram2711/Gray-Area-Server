import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, json, request
from dotenv import load_dotenv
from firebase_utils import get_newsletter, get_subscribers, db
from mail_utils import initialize_gmail_api, insert_into_template, send_email

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


if __name__ == '__main__':
    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(send_email, 'interval', seconds=15, args=[get_subscribers(), 'Daily newsletter', insert_into_template(get_newsletter())])

    port = int(os.environ.get('PORT', 5000))
    api.run(host='0.0.0.0', port=port)

    # input("Press enter to exit.")
    sched.shutdown()
