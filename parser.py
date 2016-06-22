#!/usr/bin/env python
# Info
# Rating 1 Star = 38px


from bs4 import BeautifulSoup
import urllib.request
import sqlite3
import os
import re
import progressbar

line_separator = "=" * 50

connector = sqlite3.connect('Baskino.db')

db = connector.cursor()

# Variables
baskino_url = "http://baskino.club"

# Creating labels dir for movie preview
if not os.path.exists('./movies/thumbnails'):
    os.makedirs('./movies/thumbnails', 755, 1)


class BasKinoParser:
    def __init__(self):
        pass

    def recreate_tables(self):
        db.execute("DROP TABLE IF EXISTS categories")
        db.execute("DROP TABLE IF EXISTS movies")
        db.execute("CREATE TABLE IF NOT EXISTS `categories` ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "title TEXT NOT NULL,"
                   "link TEXT NOT NULL,"
                   "pages INTEGER NOT NULL DEFAULT 1)")
        db.execute("CREATE TABLE IF NOT EXISTS `movies` ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "category_id INTEGER NOT NULL DEFAULT 1,"
                   "title TEXT,"
                   "link CHAR(200) NOT NULL,"
                   "rating FLOAT DEFAULT 0.00,"
                   "released INTEGER(4))")

    def category_parser(self):
        print(line_separator)
        html = urllib.request.urlopen(baskino_url).read()
        bs_body = BeautifulSoup(html, "html.parser")
        categories_list = bs_body.find("ul", class_="list6 wrapper")
        categories = BeautifulSoup(str(categories_list).encode('utf8'), "html.parser").find_all('li')

        for category in categories:
            category_link = category.a['href']
            category_title = category.a.text
            pages_count = self.get_pages_count(baskino_url + category_link)

            print("Adding", category_title, "(" + pages_count + " pages)")
            db.execute("INSERT INTO categories VALUES (NULL, ?, ?, ?)", [
                category_title, category_link, pages_count
            ])

        connector.commit()
        print(line_separator)

    def get_pages_count(self, link):
        page = urllib.request.urlopen(link).read()
        content = BeautifulSoup(page, "html.parser").find('div', class_='navigation')
        total_pages = BeautifulSoup(str(content).encode('utf8'), "html.parser").find_all('a')
        total_pages_parser = BeautifulSoup(str(total_pages[-2]).encode('utf8'), 'html.parser').find('a')
        return total_pages_parser.text

    def get_categories(self):
        categories_list = db.execute("SELECT * FROM categories").fetchall()

        for cat in categories_list:
            self.get_movies_from_cat(baskino_url + cat[2], cat[0], cat[3], cat[1])

    def get_movies_from_cat(self, cat, cat_id, pages, cat_name):
        with progressbar.ProgressBar(
                max_value=pages,
                marker=progressbar.RotatingMarker(),
                widgets=[
                    progressbar.FormatLabel(
                                                        "Processed %(value)d pages / " +
                                                        str(pages) + ' from ' + str(cat_name) +
                                                        " in %(elapsed)s"
                    )
                ]
        ) as p:
            for page in range(1, pages):
                p.update(page)

                if page == 1:
                    page_link = cat
                else:
                    page_link = str(cat) + 'page/' + str(page) + '/'

                html_data = BeautifulSoup(urllib.request.urlopen(page_link).read(), "html.parser") \
                    .find_all('div', class_="shortpost")

                if not os.path.exists('./movies/thumbnails/' + str(cat_id) + '/'):
                    os.makedirs('./movies/thumbnails/' + str(cat_id) + '/', 755, 1)

                for movie in html_data:
                    tmp_data = BeautifulSoup(str(movie).encode('utf8'), 'html.parser')

                    movie_rating = "{:.2f}".format(float(tmp_data.find('li', class_='current-rating').text) / 38)
                    movie_title = tmp_data.find('div', class_='posttitle').a.text
                    movie_link = tmp_data.find('div', class_='posttitle').a['href']
                    movie_img = tmp_data.find('div', class_='postcover').img['src']
                    movie_released = tmp_data.find('div', class_='rinline')
                    released = re.search(re.compile('Год выпуска: (\d+)'), str(movie_released)).group(1)

                    db.execute("INSERT INTO movies VALUES (NULL , ?, ?, ?, ?, ?)", [
                        cat_id, movie_title, movie_link, movie_rating, released
                    ])
                    last_id = db.execute("SELECT LAST_INSERT_ROWID() FROM movies").fetchone()

                    urllib.request.urlretrieve(movie_img,
                                               './movies/thumbnails/' + str(cat_id) + '/' + str(last_id[0]) + '.png')
                connector.commit()
