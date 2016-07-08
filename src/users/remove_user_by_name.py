import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db import DBConnection

if __name__ == "__main__":
    first_name = sys.argv[1]
    last_name = sys.argv[2]
    with DBConnection() as db:
        db.remove_user((first_name, last_name), "name")