import openai
import urllib.request

from firebase_utils import save_articles_to_firebase

'''
Call this function, GPT3 will generate article and send it to firebase
source: a dictionary, read line 23-27
send_to_db: if False, do not send the article do firebase. in case we fill the db up with too many trash drafts during testing. No matter it is set to True or False, the generated article can be viewed in the "response.txt" file. The generated image can be viewed in "thumbnail.jpg".
'''


def generate_article(source, send_to_db=False):
    # setup openai api key
    openai.api_key = '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'

    # read sources from text file if input source is none
    if source is None:
        with open('source_a.txt', 'r', encoding='utf-8') as file:
            source_a = file.read()
        with open('source_b.txt', 'r', encoding='utf-8') as file:
            source_b = file.read()
        with open('neutral.txt', 'r', encoding='utf-8') as file:
            source_neutral = file.read()

    # else read the input
    else:
        source_a = source['pro']
        source_b = source['neg']
        source_neutral = source['neu']

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

    # generate narrations
    response_a = openai.Completion.create(
        model="text-davinci-003",
        prompt=source_a + f'\n\n Rewrite the above content\'s argument in {narration_len} words.',
        temperature=0.1,
        max_tokens=narration_len * 4,
        best_of=3
    )
    narration_a = response_a.choices[0].text
    response_a = openai.Completion.create(
        model="text-davinci-003",
        prompt=narration_a + f'\n\n Rewrite the above content so that' + audience_level,
        temperature=0.1,
        max_tokens=narration_len * 4,
    )
    narration_a = response_a.choices[0].text

    response_b = openai.Completion.create(
        model="text-davinci-003",
        prompt=source_b + f'\n\n Rewrite the above content\'s argument in {narration_len} words.',
        temperature=0.1,
        max_tokens=narration_len * 4,
        best_of=3
    )
    narration_b = response_b.choices[0].text
    response_b = openai.Completion.create(
        model="text-davinci-003",
        prompt=narration_b + f'\n\n Rewrite the above content so that' + audience_level,
        temperature=0.1,
        max_tokens=narration_len * 4,
    )
    narration_b = response_b.choices[0].text

    # generate sub-heading
    response_title_a = openai.Completion.create(
        model="text-davinci-003",
        prompt=source_a + f'\n\n In five words, summarize the above argument\'s perspective.',
        temperature=0.1,
        max_tokens=16
    )
    title_a = response_title_a.choices[0].text.replace('"', '').replace('.', '')

    response_title_b = openai.Completion.create(
        model="text-davinci-003",
        prompt=source_b + f'\n\n In five words, summarize the above argument\'s perspective.',
        temperature=0.1,
        max_tokens=16
    )
    title_b = response_title_b.choices[0].text.replace('"', '').replace('.', '')

    # generate summary
    response_summary = openai.Completion.create(
        model="text-davinci-003",
        prompt=source_neutral + f'\n\n Summarize the above content using {summary_len} words.',
        temperature=0.2,
        max_tokens=summary_len * 4,
        best_of=3
    )
    summary = response_summary.choices[0].text
    response_summary = openai.Completion.create(
        model="text-davinci-003",
        prompt=summary + f'\n\n Rewrite the above content so that' + audience_level,
        temperature=0.1,
        max_tokens=summary_len * 4,
    )
    summary = response_summary.choices[0].text

    # generate category
    response_category = openai.Completion.create(
        model="text-davinci-003",
        prompt=summary + f'\n\n The above news article falls into the category: ',
        temperature=0,
        max_tokens=16,
    )
    category = response_category.choices[0].text.replace('.', '').replace('\n', '')

    # generate title
    response_title = openai.Completion.create(
        model="text-davinci-003",
        prompt=summary + f'\n\n Use the above context to generate a news article title in a neutral position.',
        temperature=0.1,
        max_tokens=64,
        best_of=5
    )
    title = response_title.choices[0].text.replace('"', '')

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
    with open("response.txt", "w") as text_file:
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
    urllib.request.urlretrieve(image_url, "thumbnail.jpg")

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

    return article
