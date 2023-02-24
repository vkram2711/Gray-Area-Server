import openai
import pandas as pd
from transformers import pipeline
from news_utils import get_articles_description
from timeit import default_timer as timer

# API Key
openai.api_key = "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"


def keywords_from_query(user_query):
    start = timer()

    # Generate search input for news
    response = openai.Completion.create(model="text-davinci-003",
                                        prompt="Produce 3 keywords and put AND in between them for web search for this query:  " + user_query + ". Please print them as one line. Only put quotation marks to the keywords, and do not finish with 'AND'. Do not forget to close the quotations you have opened for keywords at the end.",
                                        temperature=1, max_tokens=256)
    keywords = response.choices[0].text

    end = timer()
    print(f"Keyword generation took {end - start}")
    print(keywords)
    return keywords


def sentiment_analysis(content_dict):
    start = timer()

    # Pull up a sentiment analysis out of thin air
    sentiment_pipeline = pipeline(model="finiteautomata/bertweet-base-sentiment-analysis")
    # apply sentiment analysis to the descriptions
    data = []
    for key in content_dict.keys():
        data.append(key)
    sentiment_dict = sentiment_pipeline(data)
    df = pd.DataFrame(sentiment_dict)

    end = timer()
    print(f"Sentiment analysis took: {end - start}")
    return df, data


def separate_sentiments(df):
    # seperate the positive, neutral and negative and sort them
    print(df)
    print(df["label"])
    print(df['label'] == "POS")
    pos = df[df['label'] == "POS"]
    neu = df[df['label'] == "NEU"]
    neg = df[df['label'] == "NEG"]
    pos = pos.sort_values(by=['score'], ascending=False)
    neu = neu.sort_values(by=['score'], ascending=False)
    neg = neg.sort_values(by=['score'], ascending=False)
    final_pos = take10(pos)
    final_neu = take10(neu)
    final_neg = take10(neg)
    pos_indexes = list(final_pos.index.values)
    neu_indexes = list(final_neu.index.values)
    neg_indexes = list(final_neg.index.values)

    return pos_indexes, neu_indexes, neg_indexes


# take the first 10 of each list and grab the corresponding content for them
def take10(df):
    return df.head(10)


def content_grabber(index_list, data):
    grabbed = ""
    for elem in index_list:
        grabbed += data[elem]
    return grabbed


def generate_news(query):
    content_dict = get_articles_description(keywords_from_query(query))
    df, data = sentiment_analysis(content_dict)
    pos_indexes, neu_indexes, neg_indexes = separate_sentiments(df)

    pos_grabbed = content_grabber(pos_indexes, data)
    neu_grabbed = content_grabber(neu_indexes, data)
    neg_grabbed = content_grabber(neg_indexes, data)

    return {
        "pro": pos_grabbed,
        "neu": neu_grabbed,
        "neg": neg_grabbed
    }
