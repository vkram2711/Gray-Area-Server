from newsapi import NewsApiClient

# News API Key
secret_newsapi = "237462c20ee14da78b008dd497b009be"
api = NewsApiClient(api_key=secret_newsapi)


def get_articles_description(keywords):
    # Get description:content dictionary
    content_dict = {}
    articles = api.get_everything(q=keywords)['articles']
    print(articles)
    for elem in articles:
        content_dict[elem['description']] = elem['content']

    return content_dict
