import sys
from db import DBConnection

if __name__ == "__main__":
    user_id = sys.argv[1]
    option = sys.argv[2]
    with DBConnection() as db:
        db.remove_user(user_id, option)
