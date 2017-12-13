import requests
import webbrowser
import json
from datetime import datetime
from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from config import *
import sys
import string
from wordcloud import WordCloud, STOPWORDS
from os import path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from image_path import *

base_url = 'https://www.theatlantic.com/author/'

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True
CACHE_FNAME = "atlantic_author_cache.json"
ALT_CACHE_FNAME = '_atlantic_article_cache.html'
db_connection = None
db_cursor = None

def get_connection_and_cursor():
    global db_connection, db_cursor
    if not db_connection:
        try:
            db_connection = psycopg2.connect("dbname='{0}' user='{1}' password='{2}'".format(db_name, db_user, db_password))
            print("Success connecting to database")
        except:
            print("Unable to connect to the database. Check server and credentials.")
            sys.exit(1) # Stop running program if there's no db connection.

    if not db_cursor:
        db_cursor = db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    return db_connection, db_cursor

def setup_database():
    conn, cur = get_connection_and_cursor()
    cur.execute("""
    CREATE TABLE Words (
        ID SERIAL PRIMARY KEY,
        Name VARCHAR(128) UNIQUE
        )""")

    cur.execute("""
    CREATE TABLE Authors (
        ID SERIAL PRIMARY KEY,
        Name VARCHAR(128) UNIQUE
        )""")

    cur.execute("""
    CREATE TABLE Author_words (
        ID SERIAL PRIMARY KEY,
        author_id INTEGER REFERENCES Authors(ID),
        word_id INTEGER REFERENCES Words(ID),
        times_used INTEGER
        )""")

    cur.execute ("""
    CREATE TABLE Articles (
        ID SERIAL PRIMARY KEY,
        article_text TEXT,
        author_id INTEGER REFERENCES Authors (ID),
        publish_date VARCHAR(32),
        title VARCHAR(128) UNIQUE
        )""")

    conn.commit()
    print('Setup database complete')

class Article(object):
    def __init__(self, text, author, pubdate, title):
        self.text = text
        self.author = author
        self.pubdate = pubdate
        self.title = title

class SQL_Article(object):
    def __init__(self, text, author, pubdate, title, author_id, article_id):
        self.text = text
        self.author = author
        self.pubdate = pubdate
        self.title = title
        self.author_id = author_id
        self.article_id = article_id

    def __repr__(self):
        return "THE ATLANTIC ARTICLE: {0} by {1}".format(self.article_id, self.author_id)

    def __contains__(self, inp):
        return inp in self.text

class word_class(object):
    def __init__(self, word, ID, count=0):
        self.name = word
        self.ID = ID
        self.count = count

    def __str__(self):
        return "{} | {}".format(self.name, self.count)

    def __contains__(self, inp):
        return inp == self.name

    def increase_ct(self, count):
        self.count = self.count+count

try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

def has_cache_expired(timestamp_str, expire_in_days):
    now = datetime.now()
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)
    delta = now - cache_timestamp
    delta_in_days = delta.days

    if delta_in_days > expire_in_days:
        return True
    else:
        return False

def get_from_cache(identifier, dictionary):
    identifier = identifier.upper()
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data

def set_in_data_cache(identifier, data, expire_in_days):
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def create_request_identifier(url, name):
    salt = "theatlanticauthor"
    total_ident = url + salt + name
    return total_ident.upper() # Creating the identifier

def get_atlantic_author (name, expire_in_days=2, testing=False):
    request_url = base_url+name.lower().replace(' ', '-')+'/'
    ident = create_request_identifier(request_url, name)
    data = get_from_cache(ident,CACHE_DICTION)
    if data:
        if not testing:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if not testing:
            print("Fetching new data from {}".format(request_url))
        resp = requests.get(request_url)
        data = resp.text
        set_in_data_cache(ident, data, expire_in_days)
    return data

def get_author_articles(author_page, name, testing=False):
    bs_data = BeautifulSoup(author_page, 'html.parser')
    river = bs_data.find('ul', {'class':'river'})
    article_lis = river.find_all('li', {'class':'article'})[:10]
    article_a=[]
    for e in article_lis:
        at = e.find_all('a')
        article_a.append(at)
    article_href=[]
    for e in article_a:
        if 'author' not in e[0]['href']:
            article_href.append(e[0]['href'])
    article_html = []
    article_base_url = 'https://www.theatlantic.com/'
    for e in article_href:
        e_cache = e.split('/')
        fname = name.replace(' ', '-')+e_cache[5]+ALT_CACHE_FNAME
        try :
            with open(fname, 'r') as fl:
                a_html = fl.read()
        except:
            r = requests.get(article_base_url+e)
            a_html = r.text
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(a_html)
        article_html.append(a_html)
    if testing:
        return article_html, fname
    else:
        return article_html

def process_articles(articles):
    article_classes =[]
    words=[]
    exclude = set(string.punctuation)
    for e in articles:
        soup = BeautifulSoup(e, 'html.parser')
        art_body = soup.find('div', {'class': 'article-body'})
        ps = art_body.find_all('p')
        tstr = ''
        for l in ps:
            tstr = tstr + l.text+'\n'
        for e in tstr.split():
            new_word = ''.join(ch for ch in e if ch not in exclude)
            if new_word not in words:
                words.append(new_word)
        bio = soup.find('div', {'class': 'bio'})
        author = bio.find('a').text
        author = ''.join(ch for ch in author if ch not in exclude).lower()
        title = soup.find('h1').text
        datetime = soup.find('time')
        pubdate=datetime['datetime'].split('T')[0]
        art = Article(tstr, author, pubdate, title)
        article_classes.append(art)
    return article_classes, words

def insert_articles(list_of_articles):
    conn, cur = get_connection_and_cursor()
    for e in list_of_articles:
        cur.execute("""
        INSERT INTO Authors (Name)
        values (%s) ON CONFLICT DO NOTHING RETURNING ID""", (e.author,)) #I solved this by making it a seperate table
        try :
            author_id = cur.fetchone()
            author_id = author_id['id']
        except:
            cur.execute("SELECT Authors.id FROM Authors WHERE Authors.Name=%s", (e.author,))
            author_id = cur.fetchone()
            author_id = author_id['id']
        cur.execute("""
        INSERT INTO Articles (title, article_text, publish_date, author_id)
        values (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
        (e.title, e.text, e.pubdate, author_id))
    conn.commit()

def insert_words(list_of_words):
    conn, cur = get_connection_and_cursor()
    for e in list_of_words:
        cur.execute("""
        INSERT INTO Words (Name)
        values (%s) ON CONFLICT DO NOTHING""", (e,))
    conn.commit()

def get_author_text(name):
    conn, cur = get_connection_and_cursor()
    full_txt= ''
    sql_articles = []
    cur.execute("""
    SELECT authors.name FROM authors WHERE authors.name=%s""", (name,))
    author = cur.fetchone()
    author_name = author['name']
    cur.execute("""
    SELECT articles.article_text, articles.id, articles.author_id, articles.publish_date, articles.title
    FROM articles WHERE articles.author_id=(SELECT authors.id FROM authors WHERE authors.name=%s)""", (author_name,))
    result = cur.fetchall()
    sql_articles=[]
    atxt=''
    for e in result:
        atxt=atxt+e['article_text']
        art = SQL_Article(e['article_text'], author_name, e['publish_date'], e['title'], e['author_id'], e['id'])
        sql_articles.append(art)
    return sql_articles, atxt

def get_words():
    conn, cur = get_connection_and_cursor()
    words=[]
    cur.execute("""
    SELECT words.name, words.id FROM words""")
    ws = cur.fetchall()
    for e in ws:
        if len(e['name'])>4:
            w = word_class(e['name'], e['id'])
            words.append(w)
    return words

def count_words(sql_articles, words, num_words=5):
    a_id = sql_articles[0].author_id
    for article in sql_articles:
        for word in words:
            if word.name in article:
                word_ct = article.text.count(word.name)
                word.increase_ct(word_ct)
    sorted_words = sorted(words,key=lambda x: x.count, reverse=True)
    most_words = sorted_words[:num_words]
    return a_id, most_words

def add_most_used(author_id, words):
    conn, cur = get_connection_and_cursor()
    for e in words:
        cur.execute("""
        SELECT author_words.id
        from author_words
        WHERE author_words.word_id=%s AND author_words.author_id=%s""",
        (e.ID,author_id))
        wd = cur.fetchone()
        if wd!=None:
            cur.execute("""
            UPDATE author_words SET times_used=%s  WHERE author_words.id=%s""",(e.count,wd['id']))
        else:
            cur.execute("""
            INSERT INTO author_words (author_id, word_id, times_used)
            values (%s, %s, %s)""",
        (author_id, e.ID, e.count))
    conn.commit()

def gen_word_cloud(name, words, shape=None, testing=False):
    d = path.dirname(__file__)
    if shape:
        mask = np.array(Image.open(path.join(d, shape)))
        wc = WordCloud(background_color="white", max_words=len(words), mask=mask)
    else:
        wc = WordCloud(background_color="white", max_words=len(words))
    wc.generate(words)
    wc.to_file(path.join(d, name))
    if not testing:
        plt.imshow(wc, interpolation='bilinear')
        plt.axis("off")
        plt.show()
    return name

def get_most_used_words(name, testing=False):
    conn, cur = get_connection_and_cursor()
    cur.execute("""
    SELECT words.name, author_words.times_used
    FROM words
    LEFT JOIN author_words ON words.id=author_words.word_id
    WHERE author_words.author_id=
    (SELECT authors.id FROM authors WHERE authors.name=%s)""",
    (name,))
    most_used_words = cur.fetchall()
    if testing:
        cur.execute("""
        SELECT authors.id FROM authors WHERE authors.name=%s""",
        (name,))
        a_id=cur.fetchone()
        return most_used_words, a_id
    else:
        return most_used_words

def clear_sql():
    cur.execute("""
    DELETE FROM author_words, words, authors, articles""")
    conn.commit()
if __name__ == '__main__':
    command = None
    command = sys.argv[1]

    if command == 'setup':
        print('setting up database')
        setup_database()
    elif command == 'search':
        CACHE_DICTION=open_cache()
        inp = input('Which Atlantic author would you like to search for: ')
        d = get_atlantic_author(inp)
        f = get_author_articles(d, inp)
        articles, words = process_articles(f)
        insert_words(words)
        insert_articles(articles)
    elif command == "cloud":
        inp = input('Which Atlantic author would you like to generate a wordcloud: ')
        img = "the-cloud.jpg"
        art_list, text = get_author_text(inp)
        fnam = inp+'.png'
        if impath:
            gen_word_cloud(fnam, text, impath)
        else:
            gen_word_cloud(fnam, text)
    elif command == "add_most_used":
        inp = input('Which Atlantic author would you like to add most used words for: ')
        art_list, text = get_author_text(inp)
        wds = get_words()
        yn = input('Would you like to get the default number of words (5), or a custom number y/n? ')
        if yn == 'y':
            y = input('How many words would you like to get? (enter an integer) ')
            ID, used_words =count_words(art_list, wds, y)
        else:
            ID, used_words =count_words(art_list, wds)
        add_most_used(ID, used_words)
    elif command == "get_most_used":
        inp = input('Which Atlantic author would you like to get the most used words for: ')
        mu = get_most_used_words(inp)
        print (type(mu))
        print (mu)
        for e in mu:
            print (e['name'], '|', e['times_used'])
    elif command==clear:
        clear_sql()
