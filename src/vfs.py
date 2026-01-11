# vfs.py
import os
import copy

class VirtualFileSystem:
    def __init__(self, root_path=None, fs_data=None):
        if fs_data is not None:
            self.fs = fs_data
        elif root_path and os.path.exists(root_path):
            self.fs = self._load_from_path(root_path)
        else:
            self.fs = {"/": {}}

    def _load_from_path(self, root_path):
        fs = {}
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Get the relative path from the root
            rel_path = os.path.relpath(dirpath, root_path)
            if rel_path == ".":
                rel_path = ""

            # Navigate to the correct node in the fs
            parts = rel_path.split(os.sep)
            node = fs
            for part in parts:
                if part:
                    node = node.setdefault(part, {})
            
            # Add files
            for filename in filenames:
                try:
                    with open(os.path.join(dirpath, filename), 'r') as f:
                        node[filename] = f.read()
                except (IOError, UnicodeDecodeError) as e:
                    node[filename] = f"Error reading file: {e}"

        return {"/": fs}

    def _get_path(self, path):
        parts = path.strip("/").split("/")
        node = self.fs["/"]
        for part in parts:
            if part == "":
                continue
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node

    def list_files(self, path="."):
        if path == ".":
            path = "/"
        node = self._get_path(path)
        if node is None or not isinstance(node, dict):
            return "Path not found or not a directory."
        return list(node.keys())

    def create_file(self, file_path, content):
        parts = file_path.strip("/").split("/")
        filename = parts.pop()
        if not filename:
            return "Invalid file path."
            
        dir_path = "/" + "/".join(parts)
        node = self._get_path(dir_path)
        
        if node is None or not isinstance(node, dict):
            # Automatically create the directory if it doesn't exist.
            node = self.fs["/"]
            for part in parts:
                if part == "":
                    continue
                if part not in node:
                    node[part] = {}
                node = node[part]

        node[filename] = content
        return f"File '{file_path}' created successfully."

    def read_file(self, file_path):
        node = self._get_path(file_path)
        if node is None or isinstance(node, dict):
            return "File not found or is a directory."
        return node

    def delete_file(self, file_path):
        parts = file_path.strip("/").split("/")
        filename = parts.pop()
        if not filename:
            return "Invalid file path."
        
        dir_path = "/" + "/".join(parts)
        node = self._get_path(dir_path)

        if node is None or not isinstance(node, dict) or filename not in node:
            return "File not found."
        
        del node[filename]
        return f"File '{file_path}' deleted successfully."

    def print_fs(self, path="/", indent=0):
        node = self._get_path(path)
        if node is None:
            return

        for name, content in list(node.items()):
            print("  " * indent + f"- {name}")
            if isinstance(content, dict):
                self.print_fs(f"{path}/{name}".replace("//", "/"), indent + 1)

class VFS:
    _instance = None

    @classmethod
    def get_instance(cls, root_path=None, fs_data=None):
        if cls._instance is None:
            cls._instance = VirtualFileSystem(root_path, fs_data)
        return cls._instance

