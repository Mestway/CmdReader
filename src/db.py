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
import sys
from fun import pokemon_name_list
import analytics

from util import encode_url

html_rel2abs = re.compile('"/[^\s<>]*/*http')
hypothes_header = re.compile('\<\!\-\- WB Insert \-\-\>.*\<\!\-\- End WB Insert \-\-\>', re.DOTALL)


MAX_RESPONSES = 2
SIMHASH_BITNUM = 64
SIMHASH_DIFFBIT = 8

# Depending on how often we expect to be doing server updates, we might want to
# make this information persistent.
url_leases = []
url_lease_lock = threading.RLock()

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

# TODO: complete this function that detects "find" command of at least length 3 from arbitrary string
def cmd_detection(text):
    lines = text.splitlines()
    cmds = []
    for line in lines:
        if not '-' in line:
            continue
        words = line.split()
        if len(words) < 3:
            continue
        # assume at most one command per line
        cmd = []
        expecting_arg = False
        expecting_opt = False
        for word in words:
            if word == "find" and not expecting_arg and not expecting_opt:
                cmd.append(word)
                expecting_arg = False
    return cmds
 
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

    @analytics.instrumented
    def create_schema(self):
        c = self.cursor

        c.execute("CREATE TABLE IF NOT EXISTS Urls    (search_phrase TEXT, url TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS Urls_url ON Urls (url)")
        c.execute("CREATE INDEX IF NOT EXISTS Urls_sp  ON Urls (search_phrase)")

        c.execute("CREATE TABLE IF NOT EXISTS SearchContent (url TEXT, fingerprint TEXT, min_distance INT, num_cmds INT, num_visits INT, html TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS SearchContent_url ON SearchContent (url)")
        # c.execute("ALTER TABLE SearchContent ADD num_cmds INT")
        # c.execute("ALTER TABLE SearchContent ADD num_visits INT")
        c.execute("CREATE INDEX IF NOT EXISTS SearchContent_num_cmds ON SearchContent (num_cmds)")

        c.execute("CREATE TABLE IF NOT EXISTS Commands (url TEXT, cmd TEXT)")
        c.execute("CREATE INDEX IF NOT EXISTS Commands_url ON Commands (url)")

        c.execute("CREATE TABLE IF NOT EXISTS Skipped (url TEXT, user_id INT, time_stamp INT)")
        c.execute("CREATE INDEX IF NOT EXISTS Skipped_idx ON Skipped (user_id, url)")
        # c.execute("ALTER TABLE Skipped ADD time_stamp INT")

        c.execute("CREATE TABLE IF NOT EXISTS NoPairs (url TEXT, user_id INT, time_stamp INT)")
        c.execute("CREATE INDEX IF NOT EXISTS NoPairs_idx ON NoPairs (user_id, url)")
        # c.execute("ALTER TABLE NoPairs ADD time_stamp INT")

        c.execute("CREATE TABLE IF NOT EXISTS Pairs   (url TEXT, user_id INT, nl TEXT, cmd TEXT, time_stamp INT, judgement FLOAT)")
        c.execute("CREATE INDEX IF NOT EXISTS Pairs_idx ON Pairs (user_id, url)")
        # c.execute("ALTER TABLE Pairs ADD time_stamp INT")
        # c.execute("ALTER TABLE Pairs ADD judgement FLOAT")

        c.execute("CREATE TABLE IF NOT EXISTS Users   (user_id INT, first_name TEXT, last_name TEXT, alias TEXT, time_stamp INT)")
        c.execute("CREATE INDEX IF NOT EXISTS Users_userid ON Users (user_id)")
        # c.execute("ALTER TABLE Users Add alias TEXT")
        # c.execute("ALTER TABLE Users Add time_stamp INT")
        # c.execute("ALTER TABLE Users Add recall FLOAT")

        self.conn.commit()

    # --- Data management ---
    def assign_time_stamps(self):
        c = self.cursor
        c.execute("UPDATE Users SET time_stamp = 1 WHERE user_id != 23 AND user_id != 24")
        c.execute("UPDATE Users SET time_stamp = 4 WHERE user_id = 23")
        c.execute("UPDATE Users SET time_stamp = 2 WHERE user_id = 24")

        c.execute("UPDATE Pairs SET time_stamp = 1 WHERE user_id != 23 AND user_id != 24")
        c.execute("UPDATE Pairs SET time_stamp = 4 WHERE user_id = 23")
        c.execute("UPDATE Pairs SET time_stamp = 2 WHERE user_id = 24")

        c.execute("UPDATE NoPairs SET time_stamp = 1 WHERE user_id != 23 AND user_id != 24")
        c.execute("UPDATE NoPairs SET time_stamp = 4 WHERE user_id = 23")
        c.execute("UPDATE NoPairs SET time_stamp = 2 WHERE user_id = 24")

        c.execute("UPDATE Skipped SET time_stamp = 1 WHERE user_id != 23 AND user_id != 24")
        c.execute("UPDATE Skipped SET time_stamp = 4 WHERE user_id = 23")
        c.execute("UPDATE Skipped SET time_stamp = 2 WHERE user_id = 24")
        self.conn.commit()

    def record_visit(self, url):
        c = self.cursor
        c.execute("UPDATE SearchContent SET num_visits = num_visits + 1 WHERE url = ?", (url,))

    @analytics.instrumented
    def add_pairs(self, user_id, pairs):
        c = self.cursor
        time_stamp = self.get_user_time_stamp(user_id) + 1
        assert(time_stamp > 0)
        url = None
        for p in pairs:
            url = p["url"]
            c.execute("INSERT INTO Pairs (user_id, url, nl, cmd, time_stamp) VALUES (?, ?, ?, ?, ?)",
                      (user_id, encode_url(url), p["nl"].strip(), p["cmd"].strip(), time_stamp))
        self.record_visit(url)
        self.conn.commit()

    def mark_has_no_pairs(self, url, user_id):
        c = self.cursor
        time_stamp = self.get_user_time_stamp(user_id) + 1
        c.execute("INSERT INTO NoPairs (url, user_id, time_stamp) VALUES (?, ?, ?)",
                  (encode_url(url), user_id, time_stamp))
        self.record_visit(url)
        self.conn.commit()

    def skip_url(self, user_id, url):
        c = self.cursor
        time_stamp = self.get_user_time_stamp(user_id) + 1
        c.execute('INSERT INTO Skipped (url, user_id, time_stamp) VALUES (?, ?, ?)',
                  (encode_url(url), user_id, time_stamp))
        self.conn.commit()

    def pairs(self):
        c = self.conn.cursor()
        for user, url, nl, cmd, time_stamp in c.execute("SELECT user_id, url, nl, cmd, time_stamp FROM Pairs"):
            yield (user, url, nl, cmd, time_stamp)
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

    @analytics.instrumented
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

    def nopairs(self):
        c = self.conn.cursor()
        for user, url, time_stamp in c.execute("SELECT user_id, url, time_stamp FROM NoPairs"):
            yield (user, url, time_stamp)
        c.close()

    def skipped(self):
        c = self.conn.cursor()
        for user, url, time_stamp in c.execute("SELECT user_id, url, time_stamp FROM Skipped"):
            yield (user, url, time_stamp)
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

    @analytics.instrumented
    def lease_url(self, user_id, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        with url_lease_lock:
            url_leases = [ (url, user, deadline) for (url, user, deadline)
                            in url_leases if deadline > now and user != user_id ]
            # self.find_urls_with_less_responses_than(MAX_RESPONSES)
            find_urls = self.find_urls_with_reference(1) if self.get_user_time_stamp(user_id) < 1 else \
                        self.find_unannotated_urls()
            for url, count in find_urls:
                # print url
                if not self.already_annotated(user_id, url) and \
                    not self.already_skipped(user_id, url) and \
                    not self.duplicate(url):
                    lease_count = sum(1 for (url2, _, _) in url_leases if url2 == url)
                    if count + lease_count < MAX_RESPONSES:
                        url_leases.append((url, user_id, now + lease_duration))
                        print("Leased: " + url + " to " + str(user_id))
                        return url
        return None

    @analytics.instrumented
    def renew_lease(self, user_id, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        new_expiration = now + lease_duration
        with url_lease_lock:
            url = self.unlease_url(user_id)
            url_leases.append((url, user_id, new_expiration))
            # print("Renewed lease of " + url + " to " + str(user_id))

    def unlease_url(self, user_id):
        """
        Unleases the URL associated with the given user_id and returns it
        (or None if the user had no leased URL).
        """
        global url_leases
        leased_url = None
        with url_lease_lock:
            for (url, user, deadline) in url_leases:
                if user == user_id:
                    leased_url = url
                    break
            url_leases = [ (url, user, deadline) for (url, user, deadline) in url_leases \
                           if user != user_id ]
        return leased_url
        # print("Unleased " + leased_url + " from " + str(user_id))

    def random_select_url(self):
        for url, count in self.find_urls_that_is_done():
            return url, count
        for url, count in self.find_urls_with_less_responses_than():
            return url, count

    # Statistics
    def count_num_visits(self, n=10):
        c = self.conn.cursor()
        num_visits = {}
        for url, count in c.execute("SELECT SearchContent.url, count(InUse.url) as n FROM " +
                                    "SearchContent LEFT JOIN (SELECT url, user_id FROM (SELECT url, user_id FROM NoPairs " +
                                            "UNION ALL SELECT url, user_id FROM Pairs) " +
                                            "GROUP BY url, user_id) AS InUse " +
                                    "ON SearchContent.url = InUse.url " +
                                    "GROUP BY SearchContent.url"):
            num_visits[url] = count
        for url, count in num_visits.items():
            print url, count
            c.execute("UPDATE SearchContent SET num_visits = ? WHERE url = ?", (count, url))
        self.conn.commit()
        c.close()

    def find_urls_that_is_done(self, n=MAX_RESPONSES):
        c = self.conn.cursor()
        """for url, count in c.execute("SELECT SearchContent.url, " +
                                    "count(InUse.url) as n FROM " +
                                    "SearchContent LEFT JOIN (SELECT url, user_id FROM (SELECT url, user_id FROM NoPairs " +
                                            "UNION ALL SELECT url, user_id FROM Pairs) GROUP BY url, user_id) AS InUse " +
                                    "ON SearchContent.url = InUse.url " +
                                    "GROUP BY SearchContent.url HAVING n >= ?", (n,)):
        """
        for url, count in c.execute("SELECT url, num_visits FROM SearchContent WHERE num_visits >= ?", (n,)):
            yield (url, count)
        c.close()

    def find_urls_with_less_responses_than(self, n=MAX_RESPONSES):
        c = self.conn.cursor()
        for url, count in c.execute("SELECT url, num_visits FROM SearchContent WHERE num_visits < ?", (n,)):
            yield (url, count)
        c.close()

    def find_urls_with_reference(self, n=1):
        c = self.conn.cursor()
        for url, num_cmds, count in c.execute("SELECT url, num_cmds, num_visits FROM SearchContent WHERE num_visits = ? " +
                                              "AND num_cmds >= 5", (n,)):
                                              # "ORDER BY num_cmds DESC", (n,)):
            yield (url, count)

    def find_unannotated_urls(self):
        c = self.conn.cursor()
        for url, num_cmds, count in c.execute("SELECT url, num_cmds, num_visits FROM SearchContent WHERE num_visits = 0 " +
                                              "AND num_cmds >= 5"):
                                              # "ORDER BY num_cmds DESC"):
            yield (url, count)

    def num_urls_by_num_visit(self, n):
        c = self.cursor
        count = 0
        for _ in c.execute("SELECT url, num_visits FROM SearchContent WHERE num_visits = ?", (n,)):
            count += 1
        return count

    def pairs_by_url(self, url):
        c = self.conn.cursor()
        for user, url, nl, cmd in c.execute("SELECT user_id, url, nl, cmd FROM Pairs WHERE url = ?",
                                            (url,)):
            yield (user, url, nl, cmd)
        c.close()

    def no_pairs_by_url(self, url):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM NoPairs WHERE url = ?",
                                   (url,)):
            yield (user, url)
        c.close()

    def skipped_by_url(self, url):
        c = self.conn.cursor()
        for user, url in c.execute("SELECT user_id, url FROM Skipped WHERE url = ?",
                                   (url,)):
            yield (user, url)
        c.close()

    # --- Search content management ---

    # UNUSED: check if there exists unindexed URLs in the DB and add them to the index
    # def index_urls(self):
    #     for url, _ in self.find_urls_with_less_responses_than(None):
    #         self.index_url_content(url)

    def num_cmd_estimation(self):
        c = self.conn.cursor()
        # for url, _ in self.find_urls_with_less_responses_than(None):
        for url, _, _, _ in self.search_content():
            print(url)
            if self.get_url_num_cmds(url) >= 0:
                continue
            html, raw_text = extract_text_from_url(url)
            num_cmds = self.coarse_cmd_estimation(url, raw_text)
            print "%s estimated number = %d" % (url, num_cmds)
            c.execute('UPDATE SearchContent SET num_cmds = ? WHERE url = ?', (num_cmds, url))
        self.conn.commit() 

    @analytics.instrumented
    def index_url_content(self, url):
        if self.url_indexed(url):
            print(url + " already indexed")
            return
        print("Indexing " + url)
        html, raw_text = extract_text_from_url(url)
        num_cmds = self.coarse_cmd_estimation(url, raw_text)

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
        c.execute("INSERT INTO SearchContent (url, fingerprint, min_distance, num_cmds, num_visits, html) VALUES (?, ?, ?, ?, ?, ?)",
                  (url, str(fingerprint), min_distance, num_cmds, 0, ensure_unicode(html)))
        self.conn.commit()

    def coarse_cmd_estimation(self, url, text):
        lines = text.splitlines()
        num_cmds = 0
        c = self.cursor
        for line in lines:
            if not 'find ' in line:
                continue
            if len(line) <= 5:
                continue
            if len(line) > 10 and not '-' in line:
                continue
            num_cmds += 1
            c.execute("INSERT INTO Commands (url, cmd) VALUES (?, ?)", (url, line))
        if num_cmds > 0:
            self.conn.commit()
        return num_cmds

    def url_indexed(self, url):
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM SearchContent WHERE url = ? LIMIT 1", (url,)):
            return True
        return False

    def get_url_num_cmds(self, url):
        c = self.cursor
        for _, num_cmds in c.execute("SELECT url, num_cmds FROM SearchContent WHERE url = ?", (url,)):
            return num_cmds

    def get_url_html(self, url):
        c = self.cursor
        for _, html in c.execute("SELECT url, html FROM SearchContent WHERE url = ?", (url,)):
            with open("temp.html", 'w') as o_f:
                o_f.write(html)
            return html

    def search_content(self):
        c = self.conn.cursor()
        for url, fingerprint, min_distance, num_cmds, num_visits in \
                c.execute("SELECT url, fingerprint, min_distance, num_cmds, num_visits FROM SearchContent " +
                          "WHERE min_distance > ? " +
                          "ORDER BY num_cmds DESC", (SIMHASH_DIFFBIT,)):
            yield (url, fingerprint, min_distance, num_cmds, num_visits)
        c.close()

    # --- User management ---

    # Statistics
    def pairs_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url, nl, cmd, time_stamp in c.execute("SELECT user_id, url, nl, cmd, time_stamp FROM Pairs " +
                                                        "WHERE user_id = ?", (user_id,)):
            yield (user, url, nl, cmd, time_stamp)
        c.close()

    def no_pairs_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url, time_stamp in c.execute("SELECT user_id, url, time_stamp FROM NoPairs " +
                                               "WHERE user_id = ?", (user_id,)):
            yield (user, url, time_stamp)
        c.close()

    def skipped_by_user(self, user_id):
        c = self.conn.cursor()
        for user, url, time_stamp in c.execute("SELECT user_id, url, time_stamp FROM Skipped " +
                                               "WHERE user_id = ?", (user_id,)):
            yield (user, url, time_stamp)
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

    # Evaluation
    def add_judgements(self, user_id, judgements):
        c = self.cursor
        for j in judgements:
            c.execute("UPDATE Pairs SET judgement = ? WHERE cmd = ? AND nl = ?",
                      (j["judgement"], j["cmd"].strip(), j["nl"].strip()))
        self.conn.commit()
        return self.get_user_precision(user_id)

    def get_user_precision(self, user_id):
        c = self.cursor
        num_evaluated = 0
        num_correct = 0
        for _, _, judgement in c.execute("SELECT cmd, nl, judgement FROM Pairs " +
                                   "WHERE user_id = ? AND judgement != -1 ", (user_id,)):
            num_correct += judgement
            num_evaluated += 1
        if num_evaluated == 0:
            # not evaluated yet
            return -1
        return num_correct / num_evaluated

    def get_user_recall(self, user_id):
        return -1

    def sample_user_annotations(self, user_id, limit=10):
        c = self.conn.cursor()
        for user, url, nl, cmd, time_stamp in c.execute("SELECT user_id, url, nl, cmd, time_stamp FROM Pairs " +
                                                        "WHERE user_id = ? AND judgement = -1 ORDER BY RANDOM() LIMIT ?",
                                                        (user_id, limit)):
            yield (user, url, nl, cmd, time_stamp)
        c.close()

    # Logistics
    def assign_aliases(self):
        c = self.cursor
        for user, _, _ in self.users():
            c.execute('UPDATE Users SET alias = ? WHERE user_id = ?', (pokemon_name_list[user-1], user))
        self.conn.commit()

    def assign_judgements(self):
        c = self.cursor
        c.execute("UPDATE Pairs SET judgement = -1")
        self.conn.commit()

    def register_user(self, first_name, last_name):
        c = self.cursor
        user_id = self.max_user_id() + 1
        alias = pokemon_name_list[user_id - 1]
        c.execute('INSERT INTO Users (user_id, first_name, last_name, alias, time_stamp) VALUES (?, ?, ?, ?, ?)',
                  (user_id, first_name.strip(), last_name.strip(), alias.decode('utf-8'), 0))
        self.conn.commit()
        return user_id

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

    # The time-stamp attribute indicates how many milestones the user has completed
    def get_user_time_stamp(self, user_id):
        c = self.cursor
        for _, time_stamp in c.execute("SELECT user_id, time_stamp FROM Users WHERE user_id = ?", (user_id,)):
            return time_stamp

    def record_milestone(self, user_id):
        if not self.user_exist(user_id):
            return -1
        c = self.cursor
        c.execute("UPDATE Users SET time_stamp = time_stamp + 1 WHERE user_id = ?", (user_id,))
        return self.get_user_time_stamp(user_id)

    def get_access_code(self, first_name, last_name):
        c = self.cursor
        for user, _, _ in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE first_name = ? AND last_name = ?",
                                    (first_name, last_name)):
            return user
        return -1

    def max_user_id(self):
        c = self.cursor
        for u, in c.execute("SELECT max(user_id) FROM Users"):
            return u

    def num_users(self):
        c = self.cursor
        num_users = len(c.execute("SELECT * FROM Users").fetchall())
        return (num_users + 1)

    def users(self):
        c = self.conn.cursor()
        for user, fname, lname, time_stamp in c.execute("SELECT user_id, first_name, last_name, time_stamp FROM Users"):
            yield (user, fname, lname, time_stamp)
        c.close()

    # inter-comparison
    def agreement_percent(self, user1, user2):
        c = self.conn.cursor()

        if not self.user_exist(user1):
            print "User %s does not exist!" % user1
            return
        if not self.user_exist(user2):
            print "User %s does not exist!" % user2
            return

        user1_pairs = collections.defaultdict(list)
        user1_nopairs = collections.defaultdict()
        user2_pairs = collections.defaultdict(list)
        user2_nopairs = collections.defaultdict()

        for (user, url, nl, cmd) in self.pairs_by_user(user1):
            user1_pairs[url].append(cmd)
        for (user, url) in self.no_pairs_by_user(user1):
            user1_nopairs[url] = None
        for (user, url, nl, cmd) in self.pairs_by_user(user2):
            user2_pairs[url].append(cmd)
        for (user, url) in self.no_pairs_by_user(user2):
            user2_nopairs[url] = None

        common_urls = set(user1_pairs.keys() + user1_nopairs.keys()) & \
                      set(user2_pairs.keys() + user2_nopairs.keys())
        print("%d common_urls" % len(common_urls))

        total_cmds = 0
        agree_cmds = 0
        for url in common_urls:
            user1_cmds = set(user1_pairs[url]) if url in user1_pairs else set()
            user2_cmds = set(user2_pairs[url]) if url in user2_pairs else set()
            print(url)
            print("User %s" % user1)
            for cmd in user1_cmds:
                print cmd
            print("User %s" % user2)
            for cmd in user2_cmds:
                print cmd
            total_cmds += len(user1_cmds | user2_cmds)
            agree_cmds += len(user1_cmds & user2_cmds)

        print("%d commands annotated in total" % total_cmds)
        print("%d commands annotated by both" % agree_cmds)
        print("percentage agreement = %f" % ((agree_cmds + 0.0) / total_cmds))
        c.close()

    ###### Danger Zone ######

    # remove records of a user from the database
    def remove_user(self, user_id, options=""):
        c = self.cursor
        if options == "name":
            first_name, last_name = user_id
            c.execute("DELETE From Users WHERE first_name = ? AND last_name = ?", (first_name, last_name))
            return

        user_id = int(user_id)
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

    # remove a specific user's annotation of a specific url
    def remove_user_annotation(self, user_id, url):
        c = self.cursor

        if not self.user_exist(user_id):
            print "User %s does not exist!" % user_id
            return

        c.execute("DELETE FROM Pairs WHERE user_id = ? AND url = ?", (user_id, url))
        print("Removed annotations of %s from user %s" % (url, user_id))

    def debugging(self, url):
        c = self.cursor
        for x in c.execute("UPDATE SearchContent SET num_visits = num_visits + 1 WHERE url = ?", (url,)):
            print x
        # c.execute("UPDATE SearchContent SET num_visits = 2 WHERE min_distance = 11 AND num_cmds = 36")

if __name__ == "__main__":
    with DBConnection() as db:
        db.create_schema()
        # db.num_cmd_estimation()
        # db.count_num_visits()
        # db.assign_time_stamps()
        # url = sys.argv[1]
        # db.debugging(url)
        db.assign_judgements()