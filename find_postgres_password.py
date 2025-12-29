"""
Find PostgreSQL Password - Try common passwords
"""

import psycopg2

COMMON_PASSWORDS = [
    "",  # Empty password
    "postgres",
    "admin",
    "password",
    "root",
    "123456",
    "admin123",
    "postgres123",
]

def try_connect(password):
    """Try to connect with given password"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password=password,
            connect_timeout=3
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

print("Trying common PostgreSQL passwords...\n")

for i, password in enumerate(COMMON_PASSWORDS, 1):
    display_pwd = f"'{password}'" if password else "(empty)"
    print(f"[{i}/{len(COMMON_PASSWORDS)}] Trying password: {display_pwd}...", end=" ")

    if try_connect(password):
        print(" SUCCESS!")
        print(f"\n[OK] Found working password: {display_pwd}")
        print(f"\nCreating .env.local file...")

        # Create .env.local
        with open(".env.local", "w") as f:
            f.write(f"# Local development database\n")
            f.write(f"DATABASE_URL=postgresql://juris_ia_user:changeme123@localhost:5432/juris_ia\n")

        print("[OK] .env.local created")
        print("\nNext step: Run the database setup:")
        print(f"  psql -U postgres -d postgres -c \"CREATE DATABASE juris_ia;\"")
        print(f"  psql -U postgres -d postgres -c \"CREATE USER juris_ia_user WITH PASSWORD 'changeme123';\"")
        print(f"  psql -U postgres -d postgres -c \"GRANT ALL PRIVILEGES ON DATABASE juris_ia TO juris_ia_user;\"")
        print(f"\nOr run the Python setup script with password: {display_pwd}")
        break
    else:
        print(" failed")
else:
    print("\n[ERROR] None of the common passwords worked.")
    print("\nPlease find your PostgreSQL password and run manually:")
    print("  1. Find pg_hba.conf file (usually in PostgreSQL installation dir)")
    print("  2. Or use pgAdmin to check connection settings")
    print("  3. Or reset password using: ALTER USER postgres PASSWORD 'newpassword';")
