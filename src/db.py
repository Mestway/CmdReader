import collections
import datetime

import socket
import ssl
import urllib2

from bs4 import BeautifulSoup
import random, string

# import scipy.sparse as ssp
from simhash import Simhash

import sqlite3
import threading

import re
from fun import pokemon_name_list

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

def ensure_unicode(content):
    if isinstance(content, str):
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError, e:
            content = content.decode('iso-8859-1')
    return unicode(content)

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
        html = urllib2.urlopen(hypothes_header + url, timeout=2)
    except urllib2.URLError, e:
        print("Error: extract_text_from_url() urllib2.URLError")
        return "", randomstr(180)
    except socket.timeout, e:
        print("Error: extract_text_from_url() socket.timeout")
        return "", randomstr(180)
    except ssl.SSLError, e:
        print("Error: extract_text_from_url() ssl.SSLError")
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
        self.conn = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def create_schema(self):
        c = self.cursor

        c.execute("CREATE TABLE IF NOT EXISTS Urls    (search_phrase TEXT, url TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS Urls_url ON Urls (url)")
        c.execute("CREATE INDEX IF NOT EXISTS Urls_sp  ON Urls (search_phrase)")

        c.execute("CREATE TABLE IF NOT EXISTS SearchContent (url TEXT, fingerprint TEXT, min_distance INT, html TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS SearchContent_url ON SearchContent (url)")

        # c.execute("ALTER TABLE SearchContent ADD html TEXT")
        # c.execute("CREATE INDEX IF NOT EXISTS SearchContent_html ON SearchContent (html)")

        c.execute("CREATE TABLE IF NOT EXISTS Skipped (url TEXT, user_id INT)")
        c.execute("CREATE INDEX IF NOT EXISTS Skipped_idx ON Skipped (user_id, url)")

        c.execute("CREATE TABLE IF NOT EXISTS NoPairs (url TEXT, user_id INT)")
        c.execute("CREATE INDEX IF NOT EXISTS NoPairs_idx ON NoPairs (user_id, url)")

        c.execute("CREATE TABLE IF NOT EXISTS Pairs   (url TEXT, user_id INT, nl TEXT, cmd TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS Pairs_idx ON Pairs (user_id, url)")

        c.execute("CREATE TABLE IF NOT EXISTS Users   (user_id INT, first_name TEXT, last_name TEXT, alias TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS Users_userid ON Users (user_id)")

        # c.execute("ALTER TABLE Users Add alias TEXT")

        # self.index_urls()
        # self.assign_aliases()

        self.conn.commit()

    # --- Data management ---

    def add_pairs(self, user_id, pairs):
        c = self.cursor
        for p in pairs:
            c.execute("INSERT INTO Pairs (user_id, url, nl, cmd) VALUES (?, ?, ?, ?)",
                      (user_id, p["url"], p["nl"].strip(), p["cmd"].strip()))
        self.conn.commit()

    def pairs(self):
        c = self.conn.cursor()
        for user, url, nl, cmd in c.execute("SELECT user_id, url, nl, cmd FROM Pairs"):
            yield (user, url, nl, cmd)
        c.close()

    def commands(self):
        c = self.conn.cursor()
        for cmd in c.execute("SELECT DISTINCT cmd FROM Pairs"):
            yield cmd
        c.close()

    # --- Query management ---

    def already_searched(self, search_phrase):
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM Urls WHERE search_phrase = ? LIMIT 1", (search_phrase,)):
            return True
        return False

    # --- URL management ---

    def add_urls(self, search_phrase, urls, caching=False):
        c = self.cursor
        for url in urls:
            if caching:
                self.index_url_content(url)
            else:
                c.execute("INSERT INTO Urls (search_phrase, url) VALUES (?, ?)", (search_phrase.strip(), url))
        self.conn.commit()
        if not caching:
            print "%d URLs remembered" % len(urls)

    def find_urls_that_is_done(self, n=MAX_RESPONSES):
        c = self.conn.cursor()
        for url, count in c.execute("SELECT Urls.url, " +
                                    "count(InUse.url) as n FROM Urls " +
                                    "LEFT JOIN (SELECT url FROM NoPairs " +
                                                "UNION ALL SELECT url FROM Pairs) " +
                                    "AS InUse ON Urls.url = InUse.url " +
                                    "GROUP BY Urls.url HAVING n >= ?", (n,)):
            yield (url, count)
        c.close()

    def find_urls_with_less_responses_than(self, user_id, n=MAX_RESPONSES):
        c = self.conn.cursor()
        for url, count in c.execute("SELECT Urls.url, " +
                                    "count(InUse.url) as n FROM Urls " +
                                    "LEFT JOIN (SELECT url FROM NoPairs " +
                                                "UNION ALL SELECT url FROM Pairs) " +
                                    "AS InUse ON Urls.url = InUse.url " +
                                    "GROUP BY Urls.url HAVING n < ?", (n,)):
            yield (url, count)
        c.close()

    def nopairs(self):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM NoPairs"):
            yield (user, url)
        c.close()

    def skipped(self):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM Skipped"):
            yield (user, url)
        c.close()

    def already_annotated(self, user_id, url):
        c = self.cursor
        if user_id:
            # print("retrieve urls annotated by the current user")
            for _ in c.execute("SELECT 1 FROM NoPairs WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
            for _ in c.execute("SELECT 1 FROM Pairs WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
        return False

    def already_skipped(self, user_id, url):
        c = self.cursor
        if user_id:
            for _ in c.execute("SELECT 1 FROM Skipped WHERE user_id = ? AND url = ? LIMIT 1", (user_id, url)):
                return True
        return False

    def duplicate(self, url):
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM SearchContent WHERE url = ? AND min_distance <= ? LIMIT 1",
                           (url, SIMHASH_DIFFBIT)):
            return True
        return False

    def mark_has_no_pairs(self, url, user_id):
        c = self.cursor
        c.execute("INSERT INTO NoPairs (url, user_id) VALUES (?, ?)", (url, user_id))
        self.conn.commit()

    def lease_url(self, user_id, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        with url_lease_lock:
            url_leases = [ (url, user, deadline) for (url, user, deadline)
                            in url_leases if deadline > now and user != user_id ]
            for url, count in self.find_urls_with_less_responses_than(user_id):
                if not self.already_annotated(user_id, url) and \
                    not self.already_skipped(user_id, url) and \
                    not self.duplicate(url):
                    lease_count = sum(1 for (url2, _, _) in url_leases if url2 == url)
                    if count + lease_count < MAX_RESPONSES:
                        url_leases.append((url, user_id, now + lease_duration))
                        print("Leased: " + url + " to " + str(user_id))
                        return url
        return None

    def renew_lease(self, user_id, leased_url, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        with url_lease_lock:
            for (url, user, deadline) in url_leases:
                if url == leased_url and user == user_id and deadline > (now + datetime.timedelta(minutes=5)):
                        # the lease hasn't expired yet
                        return
            # add fifteen more minutes to the lease
            self.unlease_url(user_id, leased_url)
            url_leases.append((url, user_id, now + lease_duration))
            # print("Renewed lease of " + url + " to " + str(user_id))

    def unlease_url(self, user_id, leased_url):
        global url_leases
        url_leases = [ (url, user, deadline) for (url, user, deadline) in url_leases \
                       if url != leased_url or user != user_id ]
        # print("Unleased: " + url + " from " + str(user_id))

    def skip_url(self, user_id, url):
        c = self.cursor
        c.execute('INSERT INTO Skipped (url, user_id) VALUES (?, ?)',
                  (url, user_id))
        self.conn.commit()

    # --- Search content management ---

    # UNUSED: check if there exists unindexed URLs in the DB and add them to the index
    # def index_urls(self):
    #     for url, _ in self.find_urls_with_less_responses_than(None):
    #         self.index_url_content(url)

    def index_url_content(self, url):
        if self.url_indexed(url):
            print(url + " already indexed")
            return
        print("Indexing " + url)
        html, raw_text = extract_text_from_url(url)
        fingerprint = Simhash(raw_text).value
        if not isinstance(fingerprint, long):
            if isinstance(fingerprint, int):
                fingerprint = long(fingerprint)
            else:
                print("Warning: fingerprint type of " + url + " is " + str(type(fingerprint)))

        min_distance = SIMHASH_BITNUM
        c = self.cursor
        for _url, _fingerprint, _min_distance in c.execute(("SELECT url, fingerprint, min_distance FROM SearchContent")):
            fingerprint_dis = distance(fingerprint, long(_fingerprint))
            if fingerprint_dis < min_distance:
                min_distance = fingerprint_dis
        c.execute("INSERT INTO SearchContent (url, fingerprint, min_distance, html) VALUES (?, ?, ?, ?)",
                  (url, str(fingerprint), min_distance, ensure_unicode(html)))
        self.conn.commit()

    def url_indexed(self, url):
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM SearchContent WHERE url = ? LIMIT 1", (url,)):
            return True
        return False

    def get_url_html(self, url):
        c = self.cursor
        for _, html in c.execute("SELECT url, html FROM SearchContent WHERE url = ?", (url,)):
            with open("temp.html", 'w') as o_f:
                o_f.write(html)
            return html

    def search_content(self):
        c = self.conn.cursor()
        for url, fingerprint, min_distance in c.execute("SELECT url, fingerprint, min_distance FROM SearchContent"):
            yield (url, fingerprint, min_distance)
        c.close()

    # --- User management ---

    def pairs_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url, nl, cmd in c.execute("SELECT user_id, url, nl, cmd FROM Pairs WHERE user_id = ?",
                                            (user_id,)):
            yield (user, url, nl, cmd)
        c.close()

    def no_pairs_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM NoPairs WHERE user_id = ?",
                                   (user_id,)):
            yield (user, url)
        c.close()

    def skipped_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM Skipped WHERE user_id = ?",
                                   (user_id,)):
            yield (user, url)
        c.close()

    def get_leaderboard(self, user_id):
        leaderboard = collections.defaultdict(int)
        for user, _, _, _, in self.pairs():
            leaderboard[user] += 1
        print_leaderboard = []
        for user, num_pairs in sorted(leaderboard.items(), key=lambda x:x[1], reverse=True)[:10]:
            if user == user_id:
                print_leaderboard.append((user, self.get_user_names(user), num_pairs))
            else:
                print_leaderboard.append((user, self.get_user_alias(user), num_pairs))
        return print_leaderboard

    def get_num_pairs_annotated(self, user_id):
        c = self.cursor
        for count in c.execute("SELECT COUNT (*) FROM Pairs WHERE user_id = ?", (user_id,)):
            return count

    def get_num_urls_annotated(self, user_id):
        c = self.cursor
        for count in c.execute("SELECT COUNT (DISTINCT url) FROM Pairs WHERE user_id = ?", (user_id,)):
            return count

    def get_num_urls_no_pairs(self, user_id):
        c = self.cursor
        for count in c.execute("SELECT COUNT (DISTINCT url) FROM NoPairs WHERE user_id = ?", (user_id,)):
            return count

    def get_num_urls_skipped(self, user_id):
        c = self.cursor
        for count in c.execute("SELECT COUNT (DISTINCT url) FROM Skipped WHERE user_id = ?", (user_id,)):
            return count

    # --- User administration ---

    def assign_aliases(self):
        c = self.cursor
        for user, _, _ in self.users():
            c.execute('UPDATE Users SET alias = ? WHERE user_id = ?', (pokemon_name_list[user-1], user))
        self.conn.commit()

    def register_user(self, user_id, first_name, last_name):
        c = self.cursor
        alias = pokemon_name_list[int(user_id) - 1]
        c.execute('INSERT INTO Users (user_id, first_name, last_name, alias) VALUES (?, ?, ?, ?)',
                  (user_id, first_name.strip(), last_name.strip(), alias))
        self.conn.commit()

    def user_exist(self, user_id):
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM Users WHERE user_id = ? LIMIT 1", (user_id,)):
            return True
        return False

    def get_user_names(self, user_id):
        c = self.cursor
        # username_prefix = "nl2cmd"
        for _, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE user_id = ?",
                                            (user_id,)):
            return fname + ' ' + lname # + ' (' + username_prefix + '%d)' % user_id

    def get_user_alias(self, user_id):
        c = self.cursor
        for _, alias in c.execute("SELECT user_id, alias FROM Users WHERE user_id = ?", (user_id,)):
            return alias

    def get_access_code(self, first_name, last_name):
        c = self.cursor
        for user, _, _ in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE first_name = ? AND last_name = ?",
                                    (first_name, last_name)):
            return user
        return -1

    def num_users(self):
        c = self.cursor
        num_users = len(c.execute("SELECT * FROM Users").fetchall())
        return (num_users + 1)

    def users(self):
        c = self.conn.cursor()
        for user, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users"):
            yield (user, fname, lname)
        c.close()

    ###### Danger Zone ######

    # remove records of a user from the database
    def remove_user(self, user_id, options=""):
        c = self.cursor

        if not self.user_exist(user_id):
            print "User %s does not exist!" % user_id
            return
        if options == "skipped_only":
            c.execute("DELETE FROM Skipped WHERE user_id = ?", (user_id,))
            print("Removed skipping history of user %d from the database" % user_id)
        elif options == "nopairs_only":
            c.execute("DELETE FROM NoPairs WHERE user_id = ?", (user_id,))
            print("Removed nopairs history of user %d from the database" % user_id)
        elif options == "complete":
            c.execute("DELETE FROM Skipped WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM NoPairs WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM Pairs WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
            print("Completely removed user %d from the database" % user_id)
        elif options == "working_trace":
            c.execute("DELETE FROM Skipped WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM NoPairs WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM Pairs WHERE user_id = ?", (user_id,))
            print("Removed trace of user %d from the database" % user_id)
        else:
            print("Unrecognized option, please try again.")
