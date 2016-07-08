import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db import DBConnection

if __name__ == "__main__":
    user_id = int(sys.argv[1])
    url = sys.argv[2]
    with DBConnection() as db:
        db.remove_user_annotation(user_id, url)