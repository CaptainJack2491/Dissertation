# tools.py
import json
from vfs import VFS


def list_files(path="."):
    """
    List all files in a given path.
    :param path: The path to list files from.
    :return: A list of files in the path.
    """
    return VFS.get_instance().list_files(path)

def create_file(file_path, content):
    """
    Create a file with the given content.
    :param file_path: The path to the file to create.
    :param content: The content to write to the file.
    """
    return VFS.get_instance().create_file(file_path, content)

def read_file(file_path):
    """
    Read the content of a file.
    :param file_path: The path to the file to read.
    :return: The content of the file.
    """
    return VFS.get_instance().read_file(file_path)

def delete_file(file_path):
    """
    Delete a file.
    :param file_path: The path to the file to delete.
    """
    return VFS.get_instance().delete_file(file_path)

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to list files from."},
                },
                "required": ["path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the file to create."},
                    "content": {"type": "string", "description": "The content to write to the file."},
                },
                "required": ["file_path", "content"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the file to read."},
                },
                "required": ["file_path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the file to delete."},
                },
                "required": ["file_path"],
            },
        }
    }
]

available_functions = {
    "list_files": list_files,
    "create_file": create_file,
    "read_file": read_file,
    "delete_file": delete_file,
}
