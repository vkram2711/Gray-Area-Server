import os

from dotenv import load_dotenv
from newsapi import NewsApiClient

load_dotenv()

api = NewsApiClient(api_key=os.environ.get('NEWSAPI'))


def get_articles_description(keywords):
    content_dict = {}
    articles = api.get_everything(q=keywords, language='en', sort_by='relevancy')['articles']
    for elem in articles:
        content_dict[elem['description']] = elem['content']

    return content_dict


def get_top_titles():
    top = api.get_top_headlines(language='en', page_size=3)
    titles = []
    for article in top['articles']:
        titles.append(article['title'])

    return titles
