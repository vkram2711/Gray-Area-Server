import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, json, request
from dotenv import load_dotenv
import news_generator
from firebase_utils import get_newsletter, get_subscribers, db
from mail_utils import initialize_gmail_api, insert_into_template, send_email
from cyber_journalist import generate_article
import news_utils
from timeit import default_timer as timer

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


@api.route('/generate_news', methods=['GET'])
def generate_news():
    start = timer()

    query = request.args.get('query')
    source = news_generator.generate_news(query)
    article = generate_article(source, True)

    end = timer()

    print(f"News generation took:{end-start}")
    return json.dumps(article)


if __name__ == '__main__':
    # sched = BackgroundScheduler()
    # sched.start()
    # sched.add_job(send_email, 'interval', seconds=15, args=[get_subscribers(), 'Daily newsletter', insert_into_template(get_newsletter())])
    news_utils.get_articles_description('"cats" AND "pets" AND "kittens" AND "felines" AND "pets adoption" AND  "cat breeds" AND "cat toys" AND "cat food" AND "cat furniture" AND "cat health"')
    port = int(os.environ.get('PORT', 5000))
    api.run(host='0.0.0.0', port=port)

    # sched.shutdown()
