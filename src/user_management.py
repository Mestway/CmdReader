from db import DBConnection

if __name__ == "__main__":
    with DBConnection() as db:
        db.remove_user(1, "")
