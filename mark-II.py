import openai
from newsapi import NewsApiClient
import pprint
import requests
import pandas as pd
from transformers import pipeline

#API Key
openai.api_key = "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"



#Generate search input for news
user_query =input("What do you want to search the news for?")
response = openai.Completion.create(model="text-davinci-003", prompt="Produce 10 keywords and put AND in between them for web search for this query:  " + user_query + ". Please print them as one line. Only put quotation marks to the keywords, and do not finish with 'AND'. Do not forget to close the quotations you have opened for keywords at the end.", temperature=1, max_tokens=256)
keywords = response.choices[0].text


#News API Key
secret_newsapi = "237462c20ee14da78b008dd497b009be"
api = NewsApiClient(api_key=secret_newsapi)


#Get description:content dictionary
content_dict = {}

for elem in api.get_everything(q=keywords)['articles']:
     content_dict[ elem['description'] ] = elem['content']

#Pull up a sentiment analysis out of thin air
sentiment_pipeline = pipeline(model="finiteautomata/bertweet-base-sentiment-analysis")

#apply sentiment analysis to the descriptions
data = []
for key in content_dict.keys():
    data.append(key)
sentiment_dict = sentiment_pipeline(data)
df = pd.DataFrame(sentiment_dict)

#seperate the positive, neutral and negative and sort them
pos = df[df['label']=="POS"]
neu = df[df['label']=="NEU"]
neg = df[df['label']=="NEG"]
pos = pos.sort_values(by=['score'], ascending=False)
neu = neu.sort_values(by=['score'], ascending=False)
neg = neg.sort_values(by=['score'], ascending=False)

#take the first 10 of each list and grab the corresponding content for them
def take10(df):
    return df.head(10)
final_pos = take10(pos)
final_neu = take10(neu)
final_neg = take10(neg)
pos_indexes = list(final_pos.index.values)
neu_indexes = list(final_neu.index.values)
neg_indexes = list(final_neg.index.values)
def content_grabber(index_list):
    grabbed = ""
    for elem in index_list:
        grabbed += data[elem]
    return grabbed
pos_grabbed = content_grabber(pos_indexes)
neu_grabbed = content_grabber(neu_indexes)
neg_grabbed = content_grabber(neg_indexes)

