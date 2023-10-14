from sqlalchemy import func, cast
from collections import defaultdict
from datetime import datetime
from sqlalchemy.types import Date
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
# import requests
# from bs4 import BeautifulSoup
# from textblob import TextBlob
# import spacy
# import newspaper
# import json
import datetime
# from selenium import webdriver

app = Flask(__name__, static_url_path='/static', static_folder='static')
# SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///article_repo.db'
db = SQLAlchemy(app)

# nlp = spacy.load("en_core_web_sm")

cache = [{"keyword": "None", "frequency": 1, "link": "None"}]
categories = ["Business", "Sports", "Politics"]


class KeywordEntry(db.Model):

    keyword = db.Column(db.String(100), nullable=False, primary_key=True)
    link = db.Column(db.String(255), nullable=False, primary_key=True)
    frequency = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date_string = db.Column(db.String(100), nullable=False, primary_key=True)
    sentiment = db.Column(db.String(255), nullable=False)
    sentiment_score = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Keyword {self.keyword}>"


# @app.route('/api/keyword_entries', methods=['POST'])
# def create_entry():
#     try:
#         data = request.get_json()
#         new_entry = KeywordEntry(
#             keyword=data['keyword'],
#             link=data['link'],
#             frequency=data['frequency'],
#             title=data['title'],
#             category=data['category'],
#             date_string=data['date_string'],
#             sentiment=data['sentiment'],
#             sentiment_score=data['sentiment_score'],)
#         db.session.add(new_entry)
#         db.session.commit()
#         return jsonify({'message': 'Entry created successfully'})
#     except Exception as e:
#         db.session.rollback()  # Rollback changes in case of an exception
#         return jsonify({'error': str(e)}), 400


@app.route('/api/keyword_entries', methods=['GET'])
def get_entries():
    try:
        entries = KeywordEntry.query.all()
        entries_data = [{'keyword': item.keyword, 'link': item.link,
                         'frequency': item.frequency, 'title': item.title,
                         'category': item.category, 'date_string': item.date_string,
                         'sentiment': item.sentiment, 'sentiment_score': item.sentiment_score} for item in entries]
        return jsonify(entries_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_entry_counts_by_month(keyword):
    # Retrieve date strings from the database
    date_strings = db.session.query(KeywordEntry.date_string).filter(
        KeywordEntry.keyword == keyword).all()

    # Parse date strings into datetime objects
    dates = [datetime.datetime.strptime(date_string, '%d/%m/%y')
             for date_string, in date_strings]

    # Extract year and month from datetime objects and count occurrences
    counts = {}
    for date in dates:
        year_month = date.strftime('%Y-%m')
        counts[year_month] = counts.get(year_month, 0) + 1

    # Convert the counts to the desired format
    result = [{'month': key, 'count': value} for key, value in counts.items()]

    return result


def get_entry_counts_and_sentiment_sum_by_month(keyword):
    # Retrieve data from the database
    entries = db.session.query(KeywordEntry.date_string, KeywordEntry.sentiment_score).filter(
        KeywordEntry.keyword == keyword).all()

    # Convert date strings to datetime objects and aggregate counts and sentiment scores
    counts = defaultdict(int)
    sentiment_sums = defaultdict(float)

    for date_string, sentiment_score in entries:
        try:
            date = datetime.datetime.strptime(date_string, '%d/%m/%y')
            year_month = date.strftime('%m-%Y')
            counts[year_month] += 1
            sentiment_sums[year_month] += sentiment_score
        except ValueError:
            # Handle invalid date strings gracefully
            pass

    # Convert aggregated data to the desired format
    result_data = [{'month': key, 'count': counts[key], 'total_sentiment_score': sentiment_sums[key]}
                   for key in set(counts.keys()) | set(sentiment_sums.keys())]
    sorted_data = sorted(result_data, key=lambda x: x['month'])
    return sorted_data


@app.route('/api/entry_counts_by_month', methods=['GET'])
def get_entry_counts_by_month_api():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({'error': 'Keyword parameter is missing.'}), 400

    counts = get_entry_counts_and_sentiment_sum_by_month(keyword)

    return jsonify(counts)


def get_sentiment_sum_by_month(keyword):
    # Assuming the date format in the database is 'dd/mm/yy'
    # Convert the date string to a datetime object with the correct format
    date_format = '%d/%m/%y'
    date_column = func.strftime(
        '%Y-%m', cast(func.strptime(KeywordEntry.date, date_format), Date)).label('month')

    # Query the database to calculate the sum of sentiment scores by month for the specified keyword
    sentiment_sum_query = db.session.query(
        date_column,
        func.sum(KeywordEntry.sentiment_score).label('total_sentiment_score')
    ).filter(KeywordEntry.keyword == keyword).group_by(date_column).all()

    return sentiment_sum_query


# def extract_keywords(article_text, num_keywords):
#     doc = nlp(article_text)

#     keywords = []

#     for sent in doc.sents:
#         noun_chunks = [chunk for chunk in sent.noun_chunks if not any(
#             is_pronoun(token) for token in chunk)]
#         keywords.extend(chunk.text for chunk in noun_chunks)

#         keywords.extend(
#             [token.lemma_ for token in sent if token.is_alpha and not token.is_stop and token.pos_ in ['NOUN', 'PROPN'] and token.pos_ != 'PRON'])

#     keyword_freq = [(keywords.count(keyword), keyword)
#                     for keyword in set(keywords)]
#     sorted_keywords = sorted(keyword_freq, reverse=True)

#     return sorted_keywords[:num_keywords]


# def extract_sentiment(clean_text, keyword):
#     sentences = []
#     tokens = nlp(clean_text)
#     for sent in tokens.sents:
#         if keyword in sent.text:
#             sentences.append((sent.text.strip()))

#     textblob_sentiment = []
#     score = 0
#     for s in sentences:
#         txt = TextBlob(s)
#         pol = txt.sentiment.polarity
#         sub = txt.sentiment.subjectivity
#         textblob_sentiment.append([s, pol, sub])
#         score += pol

#     if len(sentences) > 0:
#         return textblob_sentiment, score / len(sentences)
#     else:
#         return textblob_sentiment, score


# def is_pronoun(token):
#     # Check if the token is a pronoun based on dependency parse
#     return token.pos_ == 'PRON' or token.dep_ in ['nsubj', 'dobj', 'iobj', 'attr', 'pobj']


# def scrape_article(url):
#     article = newspaper.Article(url=url, language='en')
#     article.download()
#     article.parse()

#     soup = BeautifulSoup(article.html, 'html.parser')
#     bbc_dictionary = json.loads(
#         "".join(soup.find("script", {"type": "application/ld+json"}).contents))

#     date_published = [value for (
#         key, value) in bbc_dictionary['@graph'][0].items() if key == 'datePublished']
#     print(date_published[0])
#     date_time_obj = datetime.datetime.fromisoformat(date_published[0])
#     return (article.text, article.title, date_time_obj)


# def get_links():
#     links = []
#     feeds = [
#         # "https://www.theguardian.com/us/rss"
#         ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936",
#          "Business"),  # Business
#         ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311", "World"),  # World
#         ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10296", "Sports"),
#     ]
#     for feed, cat in feeds:

#         response = requests.get(feed)
#         webpage = response.content
#         soup = BeautifulSoup(webpage, features='xml')
#         items = soup.find_all('item')
#         for item in items[:5]:
#             link = item.find('link').text
#             links.append((link, cat))
#         # print("Number of links: ", len(links))
#         # print("Data type of last element: ", links[len(links)-1])
#     return links


# def extract_cna_links(pagesToGet, exclude=[]):
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")
#     driver = webdriver.Chrome(options=options)
#     sources = [
#         ("https://www.channelnewsasia.com/search?type%5B0%5D=article&categories%5B0%5D=Business&page=",
#          "Business"),  # Business
#         ("https://www.channelnewsasia.com/search?type%5B0%5D=article&categories%5B0%5D=Sustainability&page=",
#          "Sustainability"),  # Sustainability
#         ("https://www.channelnewsasia.com/search?type%5B0%5D=article&categories%5B0%5D=Sport&page=", "Sports"),
#     ]

#     res = []

#     for main_link, cat in sources:

#         if cat in exclude:
#             continue

#         for page in range(pagesToGet, pagesToGet+1):
#             print('processing page :', page)
#             url = main_link + str(page)

#             driver.get(url)

#             source = driver.page_source
#             soup = BeautifulSoup(source, 'html.parser')
#             links = soup.find_all('li', attrs={'class': 'ais-Hits-item'})

#             for j in links:
#                 element = j.find(
#                     "h6", attrs={'class': 'hit-name h6 list-object__heading'})
#                 Header = element.text.strip()
#                 Link = element.find('a')['href'].strip()
#                 res.append((Link, cat))

#     driver.quit()
#     print(res)
#     return res


@app.route('/')
def index():
    return render_template('index.html')


# @app.route('/update_database', methods=['POST'])
# def update_database():
#     categories_to_exclude = []
#     links = extract_cna_links(pagesToGet=1, exclude=categories_to_exclude)
#     all_keywords = []
#     seen = set()
#     num_keywords = 3  # int(request.form['num_keywords'])
#     for url, category in links:
#         try:
#             text, title, datetime_object = scrape_article(url)
#             keywords = extract_keywords(text, num_keywords)
#             if datetime_object:
#                 date_string = datetime_object.strftime('%d/%m/%y')
#             else:
#                 date_string = datetime.date.today().strftime("%d/%m/%y")
#             for keyword in keywords:
#                 sentiment, avg_score = extract_sentiment(text, keyword[1])
#                 sentiment_json = json.dumps(sentiment)
#                 entry = KeywordEntry(
#                     keyword=keyword[1],
#                     link=url,
#                     frequency=keyword[0],
#                     title=title,
#                     category=category,
#                     date_string=date_string,
#                     sentiment=sentiment_json,
#                     sentiment_score=avg_score)
#                 if entry not in seen:
#                     all_keywords.append(entry)
#                     seen.add(entry)

#         except Exception as err:
#             print('Handling run-time error')
#             print(type(err))

#     try:
#         # db.session.add_all(all_keywords)
#         for kw in all_keywords:
#             db.session.merge(kw)
#         db.session.commit()
#         return jsonify({'message': 'Entries added successfully'})
#     except Exception as e:
#         db.session.rollback()  # Rollback changes in case of an exception
#         return jsonify({'error': str(e)}), 400


@app.route('/api/get_keywords_by_date', methods=['GET'])
def get_data_by_date():
    # Get the date parameter from the request query string
    date_to_query = request.args.get('date')

    # Check if the date parameter is provided and not empty
    if not date_to_query:
        return jsonify({'error': 'Date parameter is missing or empty'}), 400
    try:
        # Convert the date string to a datetime object
        date_obj = datetime.datetime.strptime(date_to_query, '%d/%m/%y')
        today_date = datetime.datetime.today().strftime('%d/%m/%y')

        # Check if today's entry exists in database, else update required
        print(date_to_query, today_date)
        if date_to_query == today_date:
            existing_record = KeywordEntry.query.filter_by(
                date_string=date_obj.strftime('%d/%m/%y')).first()
            print(existing_record)
            if not existing_record:
                # update_database()
                pass

        # Query the database for entries with the specified date
        entries_for_date = KeywordEntry.query.filter_by(
            date_string=date_obj.strftime('%d/%m/%y')).all()

        # Process the retrieved data as needed
        data = [{'keyword': entry.keyword, 'title': entry.title,
                 'link': entry.link, 'date_string': entry.date_string,
                 'frequency': entry.frequency, 'category': entry.category,
                 'sentiment': entry.sentiment} for entry in entries_for_date]
        return jsonify(data)

    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400


@app.route('/get_article_headers_by_keyword')
def get_article_headers():
    clicked_keyword = request.args.get('keyword')

    if not clicked_keyword:
        return jsonify({'error': 'Keyword parameter is missing or empty'}), 400

    try:

        # Query the database for entries with the specified date
        entries_for_keyword = KeywordEntry.query.filter_by(
            keyword=clicked_keyword).all()

        # Process the retrieved data as needed
        data = [{'keyword': entry.keyword, 'title': entry.title,
                 'link': entry.link, 'date_string': entry.date_string,
                 'sentiment': entry.sentiment, 'date_time': datetime.datetime.strptime(entry.date_string, '%d/%m/%y')} for entry in entries_for_keyword]

        sorted_data = sorted(data, key=lambda x: x['date_time'], reverse=True)

        return jsonify(sorted_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # # Assuming you have a function to fetch article headers based on the keyword
    # article_headers = fetch_article_headers(clicked_keyword)
    # return jsonify(article_headers)


if __name__ == "__main__":
    app.run(debug=True)
    # url = "https://www.channelnewsasia.com/sport/gatland-lauds-improvement-second-tier-teams-3776531"
    # text = scrape_article(url)
    # print(scrape_article(url))
    # print(extract_cna_links(1))
