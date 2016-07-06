import sys
from db import DBConnection

if __name__ == "__main__":
    user_id = int(sys.argv[1])
    url = sys.argv[2]
    with DBConnection() as db:
        db.remove_user_annotation(user_id, url)