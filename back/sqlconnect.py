import os
import json
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


def get_policy_by_id(policy_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a policy from the policy_catalog table by its ID."""
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM policy_catalog WHERE policy_id = %s", (policy_id,))
    policy = cursor.fetchone()
    cursor.close()
    conn.close()
    return policy


def get_policy_by_name(policy_name: str) -> Optional[Dict[str, Any]]:
    """Fetches a policy from the policy_catalog table by its name."""
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM policy_catalog WHERE policy_name = %s", (policy_name,))
    policy = cursor.fetchone()
    cursor.close()
    conn.close()
    return policy


def get_user_session(phone_number: str, name: str = None, email: str = None) -> Dict[str, Any]:
    """
    Retrieves user and their context in one go. If user doesn't exist, creates them.
    If user exists, updates their name and email if provided.
    This function ensures that user creation is committed before proceeding.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Step 1: Find user by phone number
        cursor.execute("SELECT * FROM user_info WHERE phone_number = %s", (phone_number,))
        user_info = cursor.fetchone()

        # Step 2: User does not exist - Create them
        if not user_info:
            cursor.execute(
                "INSERT INTO user_info (phone_number, name, email) VALUES (%s, %s, %s)",
                (phone_number, name, email),
            )
            conn.commit()  # Commit the new user immediately
            
            # Retrieve the newly created user
            cursor.execute("SELECT * FROM user_info WHERE phone_number = %s", (phone_number,))
            user_info = cursor.fetchone()

        if not user_info:
            raise Exception("Failed to create or retrieve user.")

        user_id = user_info['user_id']

        # Step 3: Fetch or create user context
        cursor.execute("SELECT * FROM user_context WHERE user_id = %s", (user_id,))
        user_context = cursor.fetchone()

        if not user_context:
            # Check for the existence of the chat_history column
            cursor.execute("SHOW COLUMNS FROM user_context LIKE 'chat_history'")
            has_chat_history_column = cursor.fetchone() is not None

            default_context = {
                "user_id": user_id,
                "context_state": "welcome",
                "state_history": json.dumps(["welcome"]),
            }
            if has_chat_history_column:
                default_context["chat_history"] = json.dumps([])

            insert_cols = ", ".join(default_context.keys())
            placeholders = ", ".join(["%s"] * len(default_context))
            insert_query = f"INSERT INTO user_context ({insert_cols}) VALUES ({placeholders})"
            
            cursor.execute(insert_query, tuple(default_context.values()))
            conn.commit() # Commit the new context

            # Re-fetch the context
            cursor.execute("SELECT * FROM user_context WHERE user_id = %s", (user_id,))
            user_context = cursor.fetchone()

        # Step 4: Combine and deserialize data
        session_data = {**user_info, **user_context}
        
        # Deserialize JSON fields
        json_fields = ["state_history", "shown_recommendations", "retrieved_docs", "chat_history"]
        for key in json_fields:
            if key in session_data and isinstance(session_data.get(key), str):
                try:
                    session_data[key] = json.loads(session_data[key])
                except (json.JSONDecodeError, TypeError):
                    session_data[key] = [] if 'history' in key or 'docs' in key else None
        
        if not session_data.get("chat_history"):
            session_data["chat_history"] = []

        return session_data

    except mysql.connector.Error as err:
        print(f"Database error in get_user_session: {err}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_or_create_user(phone_number: str, name: str = None, email: str = None) -> Dict[str, Any]:
    """
    Implements the stateful user flow:
    1. Checks if a user exists with the given phone number.
    2. If yes, updates their info and returns the user.
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
            # Update name and email if provided
            if name or email:
                update_fields = []
                update_values = []
                if name:
                    update_fields.append("name = %s")
                    update_values.append(name)
                if email:
                    update_fields.append("email = %s")
                    update_values.append(email)
                
                if update_fields:
                    update_query = f"UPDATE user_info SET {', '.join(update_fields)} WHERE user_id = %s"
                    update_values.append(user['user_id'])
                    cursor.execute(update_query, tuple(update_values))
                    conn.commit()
                    # Re-fetch user to get updated info
                    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user['user_id'],))
                    user = cursor.fetchone()

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
            cursor.execute(
                "INSERT INTO user_info (phone_number, name, email) VALUES (%s, %s, %s)",
                (phone_number, name, email),
            )
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

    if not context:
        return {"user_id": user_id, "context_state": "welcome", "state_history": ["welcome"], "chat_history": "[]"}

    # Deserialize JSON fields
    for key in ["state_history", "chat_history", "shown_recommendations", "retrieved_docs"]:
        if key in context and isinstance(context[key], str):
            try:
                context[key] = json.loads(context[key])
            except (json.JSONDecodeError, TypeError):
                context[key] = [] if key in ["state_history", "chat_history", "shown_recommendations", "retrieved_docs"] else context[key] # Reset if invalid JSON

    return context


def update_user_info(user_id: int, updates: Dict[str, Any]):
    """Updates the user_info for a given user by their user_id, filtering for valid columns."""
    if not updates:
        return

    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Get valid column names from the user_info table
    cursor.execute("SHOW COLUMNS FROM user_info")
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

    query = f"UPDATE user_info SET {set_clause} WHERE user_id = %s"
    
    try:
        cursor.execute(query, tuple(values))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error updating user info: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def update_user_context(user_id: int, updates: Dict[str, Any]):
    """
    Updates or creates the context for a given user by their user_id.
    This function performs an "UPSERT" operation.
    """
    if not updates:
        return

    conn = get_mysql_connection()
    cursor = conn.cursor()

    try:
        # Get valid column names from the user_context table
        cursor.execute("SHOW COLUMNS FROM user_context")
        valid_columns = {row[0] for row in cursor.fetchall()}

        # Serialize JSON fields before updating
        json_fields = ["state_history", "chat_history", "shown_recommendations", "retrieved_docs"]
        for key in json_fields:
            if key in updates and not isinstance(updates[key], str):
                updates[key] = json.dumps(updates[key])

        # Filter updates to only include keys that are valid columns
        filtered_updates = {k: v for k, v in updates.items() if k in valid_columns}

        if not filtered_updates:
            return

        # Check if context already exists
        cursor.execute("SELECT context_id FROM user_context WHERE user_id = %s", (user_id,))
        context_exists = cursor.fetchone()

        if context_exists:
            # UPDATE existing context
            set_clause = ", ".join([f"`{key}` = %s" for key in filtered_updates.keys()])
            values = list(filtered_updates.values())
            values.append(user_id)
            query = f"UPDATE user_context SET {set_clause} WHERE user_id = %s"
            cursor.execute(query, tuple(values))
        else:
            # INSERT new context
            filtered_updates['user_id'] = user_id
            columns = ", ".join([f"`{key}`" for key in filtered_updates.keys()])
            placeholders = ", ".join(["%s"] * len(filtered_updates))
            values = list(filtered_updates.values())
            query = f"INSERT INTO user_context ({columns}) VALUES ({placeholders})"
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
    name: str,
    policy_id: Optional[str],
    contact_method: str,
    contact_value: str,
):
    """Creates a new lead in the lead_capture table using user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO lead_capture (user_id, name, policy_id, contact_method, contact_value)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, name, policy_id, contact_method, contact_value))
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


def log_chat_message(user_id: int, message_type: str, message: Any):
    """Logs a message to the chat_log table using user_id."""
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Convert dicts/lists to JSON strings
    if isinstance(message, (dict, list)):
        message = json.dumps(message)

    query = "INSERT INTO chat_log (user_id, message_type, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, message_type, message))
    conn.commit()
    cursor.close()
    conn.close()



def get_user_info_for_quote(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetches user information from the user_info table required for a premium quote.
    This is simplified to avoid fetching context data that is already present.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        dob, 
        gender, 
        employment_status, 
        annual_income, 
        gst_applicable
    FROM 
        user_info
    WHERE 
        user_id = %s
    """
    
    try:
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            # Convert date object to string if it exists
            if user_data.get('dob'):
                user_data['dob'] = user_data['dob'].strftime('%Y-%m-%d')
            
            # Clean up None values to avoid overwriting context with them
            user_data = {k: v for k, v in user_data.items() if v is not None}
            
        return user_data
    except mysql.connector.Error as err:
        print(f"Database error in get_user_info_for_quote: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def keyword_search_policies(query: str) -> list[Dict[str, Any]]:
    """Performs a keyword search on policy names and descriptions."""
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    search_term = f"%{query}%"
    query_sql = """
    SELECT * FROM policy_catalog
    WHERE policy_name LIKE %s OR description LIKE %s
    LIMIT 2
    """
    cursor.execute(query_sql, (search_term, search_term))
    policies = cursor.fetchall()
    cursor.close()
    conn.close()
    return policies


def save_quotation_details(user_id: int, quote_data: Dict[str, Any]):
    """Saves the user's quotation details to the user_quotations table."""
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Prepare the data for insertion
    # Ensure all keys match the column names in the user_quotations table
    columns = [
        'user_id', 'dob', 'gender', 'nationality', 'marital_status', 'education',
        'existing_policy', 'gst_applicable', 'plan_option', 'coverage_required',
        'premium_budget', 'policy_term', 'premium_payment_term', 'premium_frequency',
        'income_payout_frequency', 'quote_number', 'sum_assured', 'base_premium',
        'gst_amount', 'total_premium'
    ]
    
    # Extract values from quote_data, providing defaults for missing keys
    values = [user_id] + [quote_data.get(col) for col in columns[1:]]

    # Create the SQL query
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"INSERT INTO user_quotations ({', '.join(columns)}) VALUES ({placeholders})"

    try:
        cursor.execute(insert_query, tuple(values))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error saving quotation details: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
