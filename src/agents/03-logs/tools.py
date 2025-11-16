# tools.py
import json

def check_username(username):
    """
    Check if a username is available.
    :param username: The username to check.
    :return: True if the username is available, False otherwise.
    """
    # In a real application, this would check a database or an API.
    # For this example, we'll just pretend all usernames are available.
    return True

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_username",
            "description": "Check if a username is available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "The username to check."},
                },
                "required": ["username"],
            },
        }
    }
]

available_functions = {
    "check_username": check_username
}
