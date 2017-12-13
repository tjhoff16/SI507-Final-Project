import unittest
from si507F17_finalproject import *
import random

class Cache_tests(unittest.TestCase):
    def setUp(self):
        self.inp='david a graham'
        self.CACHE_DICTION=CACHE_DICTION
        url = base_url+self.inp.replace(' ', '-')+'/'
        self.ident = create_request_identifier(url,self.inp)

    def test_cache(self):
        self.assertTrue(self.CACHE_DICTION)

    def test_cache_time(self):
        self.assertFalse(has_cache_expired(self.CACHE_DICTION[self.ident]['timestamp'], self.CACHE_DICTION[self.ident]['expire_in_days']))

class Articles_tests(unittest.TestCase):
    def setUp(self):
        self.CACHE_DICTION=CACHE_DICTION
        self.inp = 'david a graham'
        d = get_atlantic_author(self.inp, testing=True)
        self.f, self.fname = get_author_articles(d, self.inp, testing=True)
        self.articles, self.words = process_articles(self.f)
        self.exclude = set(string.punctuation)
        self.test_art_class = Article('text','author','pubdate','title')
        self.test_html_cache=open(self.fname, 'r')

    def test_num_articles_returned(self):
        self.assertTrue(len(self.f)<=10)

    def test_punc(self):
        for ele in self.exclude:
            self.assertTrue(ele not in self.words[0])

    def test_author_name(self):
        tan_int = random.randint(0,len(self.articles))
        self.assertTrue(self.inp == self.articles[tan_int].author)

    def test_article_class(self):
        self.assertTrue(type(self.articles[1].text)==type(self.test_art_class.text))
        self.assertTrue(type(self.articles[1].pubdate)==type(self.test_art_class.pubdate))
        self.assertTrue(type(self.articles[1].title)==type(self.test_art_class.title))

    def test_article_class_type(self):
        self.assertEqual(type(self.articles[1]),type(self.test_art_class))
        
    def test_html_cache(self):
        self.assertTrue(self.test_html_cache)

    def tearDown(self):
        self.test_html_cache.close()

class SQL_tests(unittest.TestCase):
    def setUp(self):
        self.CACHE_DICTION=CACHE_DICTION
        self.inp = 'david a graham'
        d = get_atlantic_author(self.inp, testing=True)
        self.f = get_author_articles(d, self.inp)
        self.articles, self.words = process_articles(self.f)
        insert_words(self.words)
        insert_articles(self.articles)
        self.exclude = set(string.punctuation)
        self.test_art_class = Article('text','author','pubdate','title')
        self.art_list, self.text = get_author_text(self.inp)
        self.fnam = self.inp+'.png'
        self.words_sql = get_words()
        self.ID, self.most_words = count_words(self.art_list, self.words_sql)
        add_most_used(self.ID, self.most_words)
        self.mu,self.a_id = get_most_used_words(self.inp, testing=True)
        self.tw_int = random.randint(0,len(self.words_sql))
        self.test_word = self.words_sql[self.tw_int].name

    def test_word_insert(self):
        self.assertTrue(self.test_word in self.words)

    def test_get_words_len(self):
        self.assertTrue(len(self.words_sql[self.tw_int].name)>4)

    def test_sql_a_id(self):
        tsaid_int = random.randint(0,10)
        self.assertTrue(self.art_list[tsaid_int].author_id == self.ID)

    def test_most_words_len(self):
        self.assertTrue(len(self.most_words)==5)
        self.test_most_words = sorted(self.most_words, key=lambda x:x.count, reverse=True)
        self.assertEqual(self.most_words[0].count,self.test_most_words[0].count)

    def test_get_most_used_words_len(self):
        self.assertEqual(len(self.mu),len(self.most_words))

    def get_words_id(self):
        self.assertEqual(self.ID,self.a_id['id'])

class cloud_tests(unittest.TestCase):
    def setUp(self):
        self.CACHE_DICTION=CACHE_DICTION
        self.inp = 'david a graham'
        d = get_atlantic_author(self.inp, testing=True)
        self.f = get_author_articles(d, self.inp)
        self.articles, self.words = process_articles(self.f)
        insert_words(self.words)
        insert_articles(self.articles)
        self.art_list, self.text = get_author_text(self.inp)
        self.fnam = self.inp+'.png'
        gen_word_cloud(self.fnam, self.text, testing=True)
        dd = path.dirname(__file__)
        self.cloud_file = Image.open(path.join(dd,self.fnam))

    def test_wordcloud_input(self):
        self.assertEqual(type(self.text),type(''))

    def test_wordcloud_file(self):
        self.assertTrue(self.cloud_file)

    def tearDown(self):
        self.cloud_file.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
