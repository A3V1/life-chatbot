import os
import uuid
from typing import Any, Dict, Optional

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_mysql_connection():
    """Establishes a connection to the MySQL database."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )


def get_mysql_data() -> list[tuple]:
    """Fetches all data from the policy_catalog table."""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy_catalog")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_policy_by_name(policy_name: str) -> Optional[Dict[str, Any]]:
    """Fetches a policy from the policy_catalog table by its name."""
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM policy_catalog WHERE policy_name = %s", (policy_name,))
    policy = cursor.fetchone()
    cursor.close()
    conn.close()
    return policy


def get_or_create_user(phone_number: str) -> Dict[str, Any]:
    """
    Implements the stateful user flow:
    1. Checks if a user exists with the given phone number.
    2. If yes, returns the user.
    3. If no, creates a new user and their initial context, then returns the new user.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Step 1: Check if user exists in user_info
        cursor.execute("SELECT * FROM user_info WHERE phone_number = %s", (phone_number,))
        user = cursor.fetchone()

        # Case 1: User Exists
        if user:
            # Check if context exists
            cursor.execute("SELECT * FROM user_context WHERE user_id = %s", (user['user_id'],))
            context = cursor.fetchone()
            if not context:
                # Create context if it's missing for an existing user
                cursor.execute(
                    "INSERT INTO user_context (user_id, context_state) VALUES (%s, %s)",
                    (user['user_id'], 'welcome'),
                )
                conn.commit()
            return user

        # Case 2: User Not Found - Create new user and context
        else:
            # Insert into user_info
            cursor.execute("INSERT INTO user_info (phone_number) VALUES (%s)", (phone_number,))
            conn.commit()
            new_user_id = cursor.lastrowid

            # Insert into user_context
            cursor.execute(
                "INSERT INTO user_context (user_id, context_state) VALUES (%s, %s)",
                (new_user_id, 'welcome'),
            )
            conn.commit()

            # Fetch and return the newly created user
            cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (new_user_id,))
            new_user = cursor.fetchone()
            if not new_user:
                 raise Exception("Failed to create or retrieve user after insertion.")
            return new_user

    except mysql.connector.Error as err:
        print(f"Database error in get_or_create_user: {err}")
        conn.rollback()
        raise  # Re-raise the exception after rollback
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a user by their user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_context(user_id: int) -> Dict[str, Any]:
    """
    Fetches the current context for a given user by their user_id.
    Returns a default context if one doesn't exist.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_context WHERE user_id = %s", (user_id,))
    context = cursor.fetchone()
    cursor.close()
    conn.close()

    if context and "state_history" in context and isinstance(context["state_history"], str):
        import json
        try:
            context["state_history"] = json.loads(context["state_history"])
        except (json.JSONDecodeError, TypeError):
            context["state_history"] = [] # Reset if invalid JSON
    
    if not context:
        return {"user_id": user_id, "context_state": "welcome", "state_history": ["welcome"]}
        
    return context


def update_user_context(user_id: int, updates: Dict[str, Any]):
    """Updates the context for a given user by their user_id, filtering for valid columns."""
    if not updates:
        return

    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Get valid column names from the user_context table
    cursor.execute("SHOW COLUMNS FROM user_context")
    valid_columns = {row[0] for row in cursor.fetchall()}

    # Filter updates to only include keys that are valid columns
    filtered_updates = {k: v for k, v in updates.items() if k in valid_columns}

    if not filtered_updates:
        cursor.close()
        conn.close()
        return

    set_clause = ", ".join([f"`{key}` = %s" for key in filtered_updates.keys()])
    values = list(filtered_updates.values())
    values.append(user_id)

    query = f"UPDATE user_context SET {set_clause} WHERE user_id = %s"
    
    try:
        cursor.execute(query, tuple(values))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error updating user context: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def create_lead(
    user_id: int,
    policy_id: Optional[str],
    contact_method: str,
    contact_value: str,
):
    """Creates a new lead in the lead_capture table using user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO lead_capture (user_id, policy_id, contact_method, contact_value)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, policy_id, contact_method, contact_value))
    conn.commit()
    cursor.close()
    conn.close()


def get_chat_history(user_id: int) -> list[tuple]:
    """Fetches the chat history for a given user by their user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = "SELECT message_type, message FROM chat_log WHERE user_id = %s ORDER BY timestamp ASC"
    cursor.execute(query, (user_id,))
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    return history


def log_chat_message(user_id: int, message_type: str, message: str):
    """Logs a message to the chat_log table using user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = "INSERT INTO chat_log (user_id, message_type, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, message_type, message))
    conn.commit()
    cursor.close()
    conn.close()
