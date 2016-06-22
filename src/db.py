import sqlite3
import datetime
import threading

MAX_RESPONSES = 3

# Depending on how often we expect to be doing server updates, we might want to
# make this information persistent.
url_leases = []
url_lease_lock = threading.Lock()

class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.conn.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS Urls    (search_phrase TEXT, url TEXT)")

        c.execute("CREATE INDEX IF NOT EXISTS Urls_url ON Urls (url)")

        c.execute("CREATE TABLE IF NOT EXISTS NoPairs (url TEXT, user_id INT)")

        c.execute("CREATE TABLE IF NOT EXISTS Pairs   (url TEXT, user_id INT, nl TEXT, cmd TEXT)")

        c.execute("CREATE TABLE IF NOT EXISTS Users   (user_id INT, first_name TEXT, last_name TEXT)")

        self.conn.commit()

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

    def already_searched(self, search_phrase):
        c = self.conn.cursor()
        for _ in c.execute("SELECT 1 FROM Urls WHERE search_phrase = ? LIMIT 1", (search_phrase,)):
            return True
        return False

    def add_urls(self, search_phrase, urls):
        c = self.conn.cursor()
        for url in urls:
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

    def users(self):
        c = self.conn.cursor()
        for user, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users"):
            yield (user, fname, lname)

    def find_urls_with_less_responses_than(self, user_id, n=MAX_RESPONSES):
        c = self.conn.cursor()
        annotated_urls = set()
        if user_id:
            print("retrieve urls annotated by the current user")
            for url, _ in c.execute("SELECT url, user_id FROM NoPairs WHERE user_id = ? " +
                "UNION ALL SELECT url, user_id FROM Pairs WHERE user_id = ?", (user_id, user_id)):
                annotated_urls.add(url)
        print(annotated_urls)
        urls = []
        for url, count in c.execute("SELECT Urls.url, " +
                                    "count(InUse.url) as n FROM Urls " +
                                    "LEFT JOIN (SELECT url FROM NoPairs " +
                                                "UNION ALL SELECT url FROM Pairs) " +
                                    "AS InUse ON Urls.url = InUse.url " +
                                    "GROUP BY Urls.url HAVING n < ?", (n,)):
            if not url in annotated_urls:
                urls.append((url, count))
        return urls

    def lease_url(self, user_id, lease_duration=datetime.timedelta(minutes=15)):
        global url_leases
        now = datetime.datetime.now()
        with url_lease_lock:
            url_leases = [ (url, user, deadline) for (url, user, deadline)
                            in url_leases if deadline > now and user != user_id ]
            for url, count in self.find_urls_with_less_responses_than(user_id):
                lease_count = sum(1 for (url2, _, _) in url_leases if url2 == url)
                if count + lease_count < MAX_RESPONSES:
                    url_leases.append((url, user_id, now + lease_duration))
                    return url
        return None

    # --- User administration ---
    def get_user_names(self, user_id):
        c = self.conn.cursor()
        username_prefix = "nl2cmd"
        for user, fname, lname in c.execute("SELECT user_id, first_name, last_name FROM Users WHERE user_id = ?",
                                            (user_id,)):
            return fname + ' ' + lname # + ' (' + username_prefix + '%d)' % user_id

    def num_users(self):
        c = self.conn.cursor()
        num_users = len(c.execute("SELECT * FROM Users").fetchall())
        return (num_users + 1)

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