import sys
from db import DBConnection

if __name__ == "__main__":
    user1 = sys.argv[1]
    user2 = sys.argv[2]
    with DBConnection() as db:
        db.agreement_percent(user1, user2)