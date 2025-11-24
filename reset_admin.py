import mysql.connector
from werkzeug.security import generate_password_hash
from config import Config

def reset_admin_password():
    print("--- Admin Password Reset Tool ---")
    username = input("Enter username (default: admin): ") or 'admin'
    new_password = input("Enter new password: ")
    
    if not new_password:
        print("Password cannot be empty.")
        return

    # Generate secure hash
    hashed_pw = generate_password_hash(new_password)
    print(hashed_pw)

    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        
        if conn.is_connected():
            cursor = conn.cursor()
            # Update query
            sql = "UPDATE users SET password_hash = %s, updated_by='system_script', updated_dt=NOW() WHERE username = %s"
            cursor.execute(sql, (hashed_pw, username))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"Success! Password for '{username}' has been updated.")
            else:
                print(f"Error: User '{username}' not found.")
                
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    reset_admin_password()