#!/opt/Musica/venv/bin/python

import sys
import getpass
import mysql.connector

def enforce_venv():
    if sys.prefix == sys.base_prefix:
        print("ERROR: This script must be run using /opt/Musica/venv/bin/python")
        sys.exit(1)

def prompt(msg, required=True):
    while True:
        value = input(msg).strip()
        if value or not required:
            return value
        print("Value required.")

def connect_as_admin():
    print("\n=== Database Admin Connection ===")
    host = prompt("DB host [localhost]: ", required=False) or "localhost"
    admin_user = prompt("Admin DB user: ")
    admin_pw = getpass.getpass("Admin DB password: ")

    try:
        return mysql.connector.connect(
            host=host,
            user=admin_user,
            password=admin_pw
        )
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
        sys.exit(1)

def show_privileges(cursor, db_name, user):
    print(f"\n=== Current privileges for '{user}' on '{db_name}' ===")
    cursor.execute(f"SHOW GRANTS FOR '{user}'")
    grants = cursor.fetchall()
    found = False

    for (grant,) in grants:
        if f"ON `{db_name}`." in grant or "ON *.*" in grant:
            print(grant)
            found = True

    if not found:
        print("(No privileges on this database)")

def prompt_change():
    print("\n=== Select action ===")
    print("1) Grant privileges")
    print("2) Revoke privileges")
    print("3) Exit")

    choice = prompt("Choice [1-3]: ")
    return choice if choice in {"1", "2", "3"} else None

def grant_privileges(cursor, db_name, user):
    privs = prompt(
        "Enter privileges to GRANT (comma-separated, e.g. SELECT,INSERT): "
    )
    cursor.execute(f"GRANT {privs} ON `{db_name}`.* TO '{user}'")
    print("Privileges granted.")

def revoke_privileges(cursor, db_name, user):
    privs = prompt(
        "Enter privileges to REVOKE (comma-separated, e.g. INSERT,UPDATE): "
    )
    cursor.execute(f"REVOKE {privs} ON `{db_name}`.* FROM '{user}'")
    print("Privileges revoked.")

def main():
    enforce_venv()

    print("=== Musica DB Admin Tool ===")
    db_name = prompt("Target database name: ")
    user = prompt("Target DB user: ")

    conn = connect_as_admin()
    cursor = conn.cursor()

    try:
        show_privileges(cursor, db_name, user)
        action = prompt_change()

        if action == "1":
            grant_privileges(cursor, db_name, user)
        elif action == "2":
            revoke_privileges(cursor, db_name, user)
        else:
            print("Exiting without changes.")
            return

        conn.commit()
        print("\n=== Updated privileges ===")
        show_privileges(cursor, db_name, user)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()

