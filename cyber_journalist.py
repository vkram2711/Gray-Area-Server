import openai
import urllib.request

from firebase_utils import save_articles_to_firebase
from timeit import default_timer as timer

# setup openai api key
openai.api_key = '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'

# hyper parameters
narration_len = 150
summary_len = 75
audience_selection = [
    ' primary school students can understand it.',
    ' middle school students can understand it.',
    ' high school students can understand it.',
    ' it appeals to business CEO readers.',
    ' it appeals to general adults.',
    ' it appeals to politician readers.'
]

audience_level = audience_selection[5]
narration_types = {
    'pro': 'benefits and positive sides',
    'neu': 'neutral statement',
    'neg': 'drawbacks and negative sides'
}


def rewrite_with_wordcount(source):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=source + f'\n\n Rewrite the above content\'s argument in {narration_len} words.',
        temperature=0.1,
        max_tokens=narration_len * 4,
        best_of=3
    )


def rewrite_for_audience(narration):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=narration + f'\n\n Rewrite the above content so that' + audience_level,
        temperature=0.1,
        max_tokens=narration_len * 4,
    )


def summarize_perspective(source):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=source + f'\n\n In five words, summarize the above argument\'s perspective.',
        temperature=0.1,
        max_tokens=16
    )


def summarize_content(source):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=source + f'\n\n Summarize the above content using {summary_len} words.',
        temperature=0.2,
        max_tokens=summary_len * 4,
        best_of=3
    )


def generate_category(summary):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=summary + f'\n\n The above news article falls into the category: ',
        temperature=0,
        max_tokens=16,
    )


def generate_article_title(summary):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=summary + f'\n\n Use the above context to generate a news article title in a neutral position.',
        temperature=0.1,
        max_tokens=64,
        best_of=5
    )


def generate_image(title, category, summary, title_a, narration_a, title_b, narration_b):
    # generate image
    response_instruction = openai.Completion.create(
        prompt='A painting with a title of "' + title + '" should look like: ',
        model="text-davinci-003",
        temperature=0.6,
        max_tokens=256,
        best_of=5
    )
    instruction = response_instruction.choices[0].text

    response_instruction = openai.Completion.create(
        prompt='Replace all human names with pronouns: ' + instruction,
        model="text-davinci-003",
        temperature=0.1,
        max_tokens=256,
    )
    instruction = response_instruction.choices[0].text

    # write response
    with open("article_hand_gen/response.txt", "w") as text_file:
        text_file.write(title + '\n\n' +
                        category + '\n\n' +
                        instruction + '\n\n' +
                        summary + '\n\n' +
                        title_a + '\n\n' +
                        narration_a + '\n\n' +
                        title_b + '\n\n' +
                        narration_b)

    response_img = openai.Image.create(
        prompt='In a comic-styled drawing, ' + instruction,
        n=1,
        size="1024x1024"
    )
    image_url = response_img['data'][0]['url']

    return image_url


def generate_source(neutral, narration_type):
    return openai.Completion.create(
        model="text-davinci-003",
        prompt=neutral + f'\n\n Use the above context to generate a news article about {narration_type} of the topic.',
        temperature=0.1,
        max_tokens=narration_len * 4,
        best_of=5
    ).choices[0].text


def generate_narration(source):
    response = rewrite_with_wordcount(source)
    narration = response.choices[0].text
    response = rewrite_for_audience(narration)
    narration = response.choices[0].text
    response_title = summarize_perspective(source)
    title = response_title.choices[0].text.replace('"', '').replace('.', '')

    return narration, title


'''
Call this function, GPT3 will generate article and send it to firebase
source: a dictionary, read line 23-27
send_to_db: if False, do not send the article do firebase. in case we fill the db up with too many trash drafts during testing. No matter it is set to True or False, the generated article can be viewed in the "response.txt" file. The generated image can be viewed in "thumbnail.jpg".
'''


def get_sources(source):
    # read sources from text file if input source is none

    source_a = source['pro']
    source_b = source['neg']
    source_neutral = source['neu']

    if (source_a == '' and source_b == '' and source_neutral == '') or source_neutral == '' and (
            source_a == '' or source_b == ''):
        return {'status': 'empty narrations'}
    if source_a == '':
        source_a = generate_source(source_neutral, narration_types['pro'])

    if source_b == '':
        source_b = generate_source(source_neutral, narration_types['neg'])

    if source_neutral == '':
        source_neutral = generate_source(source_a + '\n On the other hand, ' + source_b, narration_types['neu'])

    return source_a, source_b, source_neutral


def generate_article(source, send_to_db=False):
    start = timer()

    source_a, source_b, source_neutral = get_sources(source)

    # generate narrations
    narration_a, title_a = generate_narration(source_a)
    narration_b, title_b = generate_narration(source_b)

    # generate summary
    response_summary = summarize_content(source_neutral)
    summary = response_summary.choices[0].text
    response_summary = rewrite_for_audience(summary)
    summary = response_summary.choices[0].text

    # generate title
    response_title = generate_article_title(summary)
    title = response_title.choices[0].text.replace('"', '')

    # generate category
    response_category = generate_category(summary)
    category = response_category.choices[0].text.replace('.', '').replace('\n', '')

    image_url = generate_image(title, category, summary, title_a, narration_a, title_b, narration_b)

    article = {
        'title': title,
        'category': category,
        'urlToImage': image_url,
        'description': summary,
        'title_a': title_a,
        'narration_a': narration_a,
        'title_b': title_b,
        'narration_b': narration_b,
    }

    if send_to_db:
        save_articles_to_firebase([article])

    end = timer()
    print(f"Generate Article took: {end - start}")
    return article
