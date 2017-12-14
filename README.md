***PROGRAM DESCRIPTION***
The attached python files will run a script that will first access a page for an author who has written on The Atlantic Magazine's website.
It will then acquire the 10 most recent (or fewer if the author has written less than 10) articles by that author, and collect the text, publishing date, and title for each article.
Then it will insert that article data, as well as all the words in each article, in a PostGreSQL database.
After those steps are complete, there are several output functions. One allows a user to output a wordcloud for a given author, another allows you to first find, then print in the console the most used words by each author.

***PROGRAM CONFIGURATION***
The first file you need to configure for this program is a config.py file, an example of which is included. This gives the name, username, and password to access the sql database you will need later.
The second file, if desired, is the image_path.py file. This defines an image for the wordcloud to shape itself around. IS NOT REQUIRED
You will need Python3 to run this script, and will need to install the various modules outlined in the requirements.txt. To do this, navigate to the directory and type "pip install -r requirements.txt"

***RUNNING THE PROGRAM***
All command line input must be without any punctuation
A list of commands for the program and their functions follows:
* 'python si507F17_finalproject.py setup': will setup the database needed for later stages of the program. MUST BE RUN FIRST
* 'python si507F17_finalproject.py search': allows you to search for an author, and will process/insert the data as appropriate. After this command is entered the command line will ask for an author name. It must be an exact match. There will be no visible output, but you will see insertions into your database as appropriate.
* 'python si507F17_finalproject.py cloud': This will output a wordcloud, either in a square or a shape as desired if the image_path file is configured. After entry the command line will ask for an author name. The name must be an exact match. A wordcloud image will then open, and a .png image file will also be generated.
* 'python si507F17_finalproject.py add_most_used': This command will generate and add to the database the most used words for a given author. After entry, it will ask for an author name, which must be an exact match. Then, it will ask if you want it to generate the default number of words (5), or a custom number. 'y' chooses default, 'n' custom. If custom, it will then ask for a number, which must be an integer. There will be no visible output for this function either.
* 'python si507F17_finalproject.py get_most_used': This command outputs the most used words for a given author from the database. It will ask for an author name after command entry, which must be an exact match. It will then print out the words in the form {WORD} | {TIMES USED} in the command line.
* 'python si507F17_finalproject.py clear_sql': This command is included for housekeeping/debugging purposes- it will clear all data from the SQL database, but will not delete the tables themselves.

***EXPECTED OUTPUT***
After running 'search' there should not be any command line output, but you will have at least 11 cache files and a filled database. 'cloud' will generate a saved .png file and open an image. 'get_most_used' will print its results in the command line.

***PROGRAM DETAILS***
* There is a complex caching system implementation that timestamps each author cache for 2 days, longer than that and it refetches the author page.
* Each individual article page is cached as it's own html file with a salted standardized filename.
* Text and metadata is scraped from the html using BeautifulSoup, and stored in the class Article until database insertion.
* Words are stored in a simple list pre-database insertion.
* The database has 3 basic tables:
  * words, with each word and its ID
  * authors, with each author name and their ID
  * articles, with the article text, publishing date, title, and author_id
* Words and articles are processed into classes (word_class and SQL_Article respective) after extraction from the database.
* word_class and SQL_Article allow for iteration with a __contains__ method, and SQL_Article has a __repr__ function for debugging.
* word_class defaults count to 0, and has an increase_ct() function to increase the count as appropriate.
* The most_used_words functions operate with an intermediary table, author_words, which has the word_id, author_id, times used, and id for a given record
* the wordcloud function uses the module Wordcloud to allow for easy generation

***CITATIONS AND RESOURCES***
Wordcloud module: https://github.com/amueller/word_cloud
BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
People consulted: Jacob Haspiel, Saul Hankin, Chris Bredernitz
