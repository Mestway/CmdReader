import sqlite3

class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS NoPairs (url TEXT PRIMARY KEY, user_id INT) WITHOUT ROWID")
        c.execute("CREATE TABLE IF NOT EXISTS Pairs   (url TEXT PRIMARY KEY, user_id INT, nl TEXT, cmd TEXT) WITHOUT ROWID")
        self.conn.commit()

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.conn.commit()
        self.conn.close()

    def mark_has_no_pairs(self, url, user_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO NoPairs (url, user_id) VALUES (?, ?)", (url, user_id))
        self.conn.commit()

    def add_pair(self, url, user_id, nl_text, cmd_text):
        c = self.conn.cursor()
        c.execute("INSERT INTO Pairs (url, user_id, nl, cmd) VALUES (?, ?, ?, ?)", (url, user_id, nl_text, cmd_text))
        self.conn.commit()

    def pairs(self):
        c = self.conn.cursor()
        for nl, cmd in c.execute("SELECT nl, cmd FROM Pairs"):
            yield (nl, cmd)
