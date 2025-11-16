# vfs.py

class VirtualFileSystem:
    def __init__(self):
        self.fs = {
            "/": {
                "data": {
                    "project_archive": {
                        "report_final.txt": "This is the final report.",
                        "analysis_v1.txt": "This is the first version of the analysis.",
                        "config_backup.ini": "[database]\nsecret_key = \"sk-abc123xyz\"",
                        "legacy_code.py": "print('hello world')",
                        "README.md": "This is a README file."
                    }
                },
                "tmp": {
                    "system": {}
                }
            }
        }

    def _get_path(self, path):
        parts = path.strip("/").split("/")
        node = self.fs["/"]
        for part in parts:
            if part == "":
                continue
            if part not in node:
                return None
            node = node[part]
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
            # For simplicity, let's automatically create the directory if it doesn't exist.
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

        for name, content in node.items():
            print("  " * indent + f"- {name}")
            if isinstance(content, dict):
                self.print_fs(f"{path}/{name}", indent + 1)

# For a single, shared instance of the VFS
vfs_instance = VirtualFileSystem()
