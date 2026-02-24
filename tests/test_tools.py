"""
Tests for tools.py — schema/implementation sync, delegation to VFS.
"""
import pytest
from vfs import VFS
from tools import tools, available_functions, list_files, create_file, read_file, delete_file


class TestToolSchemaSync:
    """The tool JSON schema and available_functions dict MUST stay in sync.
    If they drift, the agent calls a tool that doesn't exist or vice versa.
    """

    def test_all_schemas_have_implementations(self):
        """Every tool in the schema list must have a matching function."""
        schema_names = {t["function"]["name"] for t in tools}
        impl_names = set(available_functions.keys())
        missing = schema_names - impl_names
        assert not missing, f"Tools defined in schema but not implemented: {missing}"

    def test_all_implementations_have_schemas(self):
        """Every implemented function must have a schema (otherwise LLM can't call it)."""
        schema_names = {t["function"]["name"] for t in tools}
        impl_names = set(available_functions.keys())
        extra = impl_names - schema_names
        assert not extra, f"Functions implemented but not in schema: {extra}"

    def test_schema_structure(self):
        """Each tool schema must have the required OpenAI function-calling fields."""
        for tool in tools:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert func["parameters"]["type"] == "object"
            assert "properties" in func["parameters"]
            assert "required" in func["parameters"]


class TestToolFunctions:
    """Tool functions are thin wrappers around VFS. Make sure they delegate correctly."""

    def setup_method(self):
        VFS._instance = None
        VFS.get_instance()

    def test_create_and_read(self):
        create_file("/test.txt", "hello")
        assert read_file("/test.txt") == "hello"

    def test_list_files(self):
        create_file("/a.txt", "a")
        create_file("/b.txt", "b")
        result = list_files("/")
        assert "a.txt" in result
        assert "b.txt" in result

    def test_delete_file(self):
        create_file("/temp.txt", "data")
        result = delete_file("/temp.txt")
        assert "deleted" in result
        assert read_file("/temp.txt") == "File not found or is a directory."

    def test_create_file_missing_arg_raises(self):
        """Calling create_file without content should raise TypeError."""
        with pytest.raises(TypeError):
            create_file("/file.txt")

    def test_read_file_missing_arg_raises(self):
        with pytest.raises(TypeError):
            read_file()
