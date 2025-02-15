import mysql.connector
from mysql.connector import Error
import bcrypt

# Create connection to MySQL database
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='user_management',
            user='root',
            password='GpkTHEboss@007'  # Use your MySQL password
        )
        if connection.is_connected():
            print("Successfully connected to the database")
        return connection

    except Error as e:
        print(f"Error: {e}")
        return None

# Function to hash a password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

# Function to register a new user
def register_user(username, password, firstName, lastName, email, phone):
    connection = create_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        hashed_password = hash_password(password)

        query = """
        INSERT INTO users (username, password, firstName, lastName, email, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, hashed_password, firstName, lastName, email, phone))
        connection.commit()
        print("User registered successfully")

    except Error as e:
        print(f"Error while registering user: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Function to log in a user
def login_user(username, password):
    connection = create_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result is None:
            print("Username does not exist")
        else:
            stored_password = result[0]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                print("Login successful")
            else:
                print("Invalid password")

    except Error as e:
        print(f"Error while logging in: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Test registration and login
register_user("john_doe", "my_secure_password", "John", "Doe", "john@example.com", "1234567890")
login_user("john_doe", "my_secure_password")
