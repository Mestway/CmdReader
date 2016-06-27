import datetime

import urllib2
import socket

from bs4 import BeautifulSoup
import random, string

# import scipy.sparse as ssp
from simhash import Simhash

import sqlite3
import threading

import re

html_rel2abs = re.compile('"/[^\s<>]*/*http')
hypothes_header = re.compile('\<\!\-\- WB Insert \-\-\>.*\<\!\-\- End WB Insert \-\-\>', re.DOTALL)

MAX_RESPONSES = 3
SIMHASH_BITNUM = 64
SIMHASH_DIFFBIT = 8

# Depending on how often we expect to be doing server updates, we might want to
# make this information persistent.
url_leases = []
url_lease_lock = threading.Lock()

def distance(f1, f2):
    x = (f1 ^ f2) & ((1 << SIMHASH_BITNUM) - 1)
    ans = 0
    while x:
        ans += 1
        x &= x - 1
    return ans

def randomstr(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def remove_headers(content):
    content = re.sub(hypothes_header, '\n', content)
    return content

# convert relative paths to absolute ones
def path_rel2abs(content):
    return re.sub(html_rel2abs, '"http', content)

def extract_text_from_url(url):
    hypothes_header = "https://via.hypothes.is/"
    try:
        html = urllib2.urlopen(hypothes_header + url, timeout=1)
    except urllib2.URLError, e:
        print("extract_text_from_url() urllib2.URLError")
        return "", randomstr(180)
    except socket.timeout, e:
        print("extract_text_from_url() socket.timeout")
        return "", randomstr(180)

    html = html.read()
    html = remove_headers(html)
    html = path_rel2abs(html)
    soup = BeautifulSoup(html, "html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    # lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    # text = '\n'.join(chunk for chunk in chunks if chunk)

    return html, text

class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.conn.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS Urls    (search_phrase TEXT, url TEXT)")

        c.execute("CREATE INDEX IF NOT EXISTS Urls_url ON Urls (url)")

        c.execute("CREATE TABLE IF NOT EXISTS SearchContent (url TEXT, fingerprint TEXT, min_distance INT, html TEXT)")

        # c.execute("ALTER TABLE SearchContent ADD html TEXT")
        # c.execute("CREATE INDEX IF NOT EXISTS SearchContent_html ON SearchContent (html)")

        c.execute("CREATE TABLE IF NOT EXISTS Skipped (url TEXT, user_id INT)")

        c.execute("CREATE TABLE IF NOT EXISTS NoPairs (url TEXT, user_id INT)")

        c.execute("CREATE TABLE IF NOT EXISTS Pairs   (url TEXT, user_id INT, nl TEXT, cmd TEXT)")

        c.execute("CREATE TABLE IF NOT EXISTS Users   (user_id INT, first_name TEXT, last_name TEXT)")

        self.conn.commit()

        # self.index_urls()

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.conn.commit()
        self.conn.close()

    # --- URL management ---

    def mark_has_no_pairs(self, url, user_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO NoPairs (url, user_id) VALUES (?, ?)", (url, user_id))
        self.conn.commit()

    def add_urls(self, search_phrase, urls):
        c = self.conn.cursor()
        for url in urls:
            self.index_url_content(url)
            c.execute("INSERT INTO Urls (search_phrase, url) VALUES (?, ?)", (search_phrase, url))
        self.conn.commit()

    def add_pairs(self, user_id, pairs):
        c = self.conn.cursor()
        for p in pairs:
            c.execute("INSERT INTO Pairs (user_id, url, nl, cmd) VALUES (?, ?, ?, ?)",
                      (user_id, p["url"], p["nl"], p["cmd"]))
        self.conn.commit()

    def pairs(self):
        c = self.conn.cursor()
        for user, url, nl, cmd in c.execute("SELECT user_id, url, nl, cmd FROM Pairs"):
            yield (user, url, nl, cmd)

    def skipped(self):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM Skipped"):
            yield (user, url)

    def find_urls_with_less_responses_than(self, user_id, n=MAX_RESPONSES):
        c = self.conn.cursor()
        for url, count in c.execute("SELECT Urls.url, " +
                                    "count(InUse.url) as n FROM Urls " +
                                    "LEFT JOIN (SELECT url FROM NoPairs " +
                                                "UNION ALL SELECT url FROM Pairs) " +
                                    "AS InUse ON Urls.url = InUse.url " +
                                    "GROUP BY Urls.url HAVING n < ?", (n,)):
            if not self.already_annotated(user_id, url) and \
                not self.already_skipped(user_id, url) and \
                not self.duplicate(url):
                yield (url, count)

    def already_annotated(self, user_id, url):
        c = self.conn.cursor()
        if user_id:
            # print("retrieve urls annotated by the current user")
            for _ in c.execute("SELECT 1 FROM NoPairs WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
            for _ in c.execute("SELECT 1 FROM Pairs WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
        return False

    def already_skipped(self, user_id, url):
        c = self.conn.cursor()
        if user_id:
            for _ in c.execute("SELECT 1 FROM Skipped WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
        return False

    def duplicate(self, url):
        c = self.conn.cursor()
        for _ in c.execute("SELECT 1 FROM SearchContent WHERE url = ? AND min_distance <= ? LIMIT 1",
                           (url, SIMHASH_DIFFBIT)):
            return True
        return False

    def lease_url(self, user_id, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        with url_lease_lock:
            url_leases = [ (url, user, deadline) for (url, user, deadline)
                            in url_leases if deadline > now and user != user_id ]
            for url, count in self.find_urls_with_less_responses_than(user_id):
                print(url)
                lease_count = sum(1 for (url2, _, _) in url_leases if url2 == url)
                if count + lease_count < MAX_RESPONSES:
                    url_leases.append((url, user_id, now + lease_duration))
                    return url
        return None

    def skip_url(self, user_id, url):
        c = self.conn.cursor()
        c.execute('INSERT INTO Skipped (url, user_id) VALUES (?, ?)',
                  (url, user_id))
        self.conn.commit()

    # --- Query management ---

    def already_searched(self, search_phrase):
        c = self.conn.cursor()
        for _ in c.execute("SELECT 1 FROM Urls WHERE search_phrase = ? LIMIT 1", (search_phrase,)):
            return True
        return False

    # --- Search content management ---

    # check if there exists unindexed URLs in the DB and add them to the index
    def index_urls(self):
        for url, _ in self.find_urls_with_less_responses_than(None):
            self.index_url_content(url)

    def index_url_content(self, url):
        if self.url_indexed(url):
            return
        print("Indexing " + url)
        html, raw_text = extract_text_from_url(url)
        fingerprint = Simhash(raw_text).value
        if not isinstance(fingerprint, long):
            print("Warning: fingerprint type of " + url + " is " + str(type(fingerprint)))

        min_distance = SIMHASH_BITNUM
        c = self.conn.cursor()
        for _url, _fingerprint, _min_distance in c.execute(("SELECT url, fingerprint, min_distance FROM SearchContent")):
            fingerprint_dis = distance(fingerprint, long(_fingerprint))
            if fingerprint_dis < min_distance:
                min_distance = fingerprint_dis
            # if fingerprint_dis < _min_distance:
            #     c.execute("UPDATE SearchContent SET min_distance = ? WHERE url = ?", (fingerprint_dis, _url))
        # print(fingerprint)
        # print(min_distance)
        c.execute("INSERT INTO SearchContent (url, fingerprint, min_distance, html) VALUES (?, ?, ?, ?)",
                  (url, str(fingerprint), min_distance, unicode(html)))

    def url_indexed(self, url):
        c = self.conn.cursor()
        for _ in c.execute("SELECT 1 FROM SearchContent WHERE url = ? LIMIT 1", (url,)):
            return True
        return False

    def get_url_html(self, url):
        c = self.conn.cursor()
        for _, html in c.execute("SELECT url, html FROM SearchContent WHERE url = ?", (url,)):
            with open("temp.html", 'w') as o_f:
                o_f.write(html)
            return html

    def search_content(self):
        c = self.conn.cursor()
        for url, fingerprint, min_distance in c.execute("SELECT url, fingerprint, min_distance FROM SearchContent"):
            yield (url, fingerprint, min_distance)


    # --- User administration ---

    def register_user(self, user_id, first_name, last_name):
        c = self.conn.cursor()
        c.execute('INSERT INTO Users (user_id, first_name, last_name) VALUES (?, ?, ?)',
                  (user_id, first_name, last_name))
        self.conn.commit()

    def user_exist(self, user_id):
        c = self.conn.cursor()
        for _ in c.execute("SELECT 1 FROM Users WHERE user_id = ? LIMIT 1", (user_id,)):
            return True
        return False

    def get_user_names(self, user_id):
        c = self.conn.cursor()
        # username_prefix = "nl2cmd"
        for user, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE user_id = ?",
                                            (user_id,)):
            return fname + ' ' + lname # + ' (' + username_prefix + '%d)' % user_id

    def get_access_code(self, first_name, last_name):
        c = self.conn.cursor()
        for user, _, _ in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE first_name = ? AND last_name = ?",
                                    (first_name, last_name)):
            return user
        return -1

    def num_users(self):
        c = self.conn.cursor()
        num_users = len(c.execute("SELECT * FROM Users").fetchall())
        return (num_users + 1)

    def users(self):
        c = self.conn.cursor()
        for user, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users"):
            yield (user, fname, lname)

    ###### Danger Zone ######

    # remove records of a user from the database
    def remove_user(self, user_id, options="complete"):
        c = self.conn.cursor()
        c.execute("DELETE FROM Skipped WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM NoPairs WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM Pairs WHERE user_id = ?", (user_id,))
        if options == "complete":
            c.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
            print("Completely removed user %d from the database" % user_id)
        else:
            print("Removed trace of user %d from the database" % user_id)




