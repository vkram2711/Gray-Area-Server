import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, json, request
from dotenv import load_dotenv
import datetime as dt
import cyber_journalist
import firebase_utils
import mail_utils
import news_generator
import news_utils
from firebase_utils import get_newsletter, get_subscribers, db
from mail_utils import initialize_gmail_api, insert_into_template, send_email
from cyber_journalist import generate_article
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


'''

@api.route('/generate_news', methods=['GET'])
def generate_news():
    start = timer()

    query = request.args.get('query')
    source = news_generator.generate_news(query)
    article = generate_article(source, True)

    end = timer()

    print(f"News generation took:{end - start}")
    return json.dumps(article)


@api.route('/generate_newsletter', methods=['GET'])
def generate_newsletter():
    titles = news_utils.get_top_titles()
    source = news_generator.generate_news(titles[0])
    article = generate_article(source, True)
    return json.dumps(article)
'''


@api.route('/get_newsletter', methods=['GET'])
def get_newsletter():
    return json.dumps(firebase_utils.get_newsletter())


if __name__ == '__main__':
    current_time = dt.datetime.utcnow()

    # Create a query to listen for changes on the "my_collection" collection
    query = db.collection('subscribers')

    # Listen for realtime updates on the query
    query_watch = query.on_snapshot(firebase_utils.on_snapshot)

    # sched = BackgroundScheduler()
    # sched.start()
    # sched.add_job(send_email, 'interval', seconds=15, args=[get_subscribers(), 'Daily newsletter', insert_into_template(get_newsletter())])
    # instruction = cyber_journalist.image_prompt_generator('As winter weather warnings, blizzards, and ice take effect across the United States, 65 million people are now under winter weather alerts from California to New York. This storm has the potential to cause hazardous travel conditions and bring snow and freezing rain. Politicians should take this storm seriously and ensure that their constituents are prepared for the potential impacts. It is essential that all necessary precautions are taken to ensure the safety of the public')
    # instruction = cyber_journalist.image_prompt_generator('Andrew Tate, a British-American social media influencer, is being investigated by Romanian prosecutors for suspected involvement in organized crime. Evidence against him includes a video of him promoting a strategy for avoiding taxes on bitcoin, and authorities have seized some of his expensive car collection. His brother and two Romanians are also in custody, and forensic searches of mobile phones and laptops are being conducted. A recent poll revealed that more 16 and 17-year-old boys had watched Tate’s videos than knew who the Chancellor of the Exchequer, Rishi Sunak, was.')
    # instruction = cyber_journalist.image_prompt_generator('President Biden has had a successful first term in office, and many are wondering if he should run for re-election in 2024. Questions have been raised about whether Biden is the best candidate to beat the Republicans, and if his age will be a factor in the election. It is uncertain if Biden, who would be in his mid-80s if re-elected, would be a capable leader of the United States. While Biden has done a good job so far, it is unclear who else could be a viable alternative if he decides not to run again')
    # print(cyber_journalist.generate_image(instruction))
    #news_generator.top_newsletter()
    #mail_utils.send_email(firebase_utils.get_subscribers(), 'Daily Newsletter', insert_into_template(firebase_utils.get_newsletter()))
    port = int(os.environ.get('PORT', 5000))
    api.run(host='0.0.0.0', port=port)

    # sched.shutdown()
