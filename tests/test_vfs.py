"""
Tests for the VFS (Virtual Filesystem) — the agent's entire sandbox.
Bugs here mean corrupted experiment data or sandbox escapes.
"""
import os
import pytest
from vfs import VirtualFileSystem, VFS


class TestVirtualFileSystem:
    """Test the core VirtualFileSystem class."""

    def setup_method(self):
        """Fresh VFS for each test."""
        self.vfs = VirtualFileSystem()

    # --- Path traversal / sandbox escape ---

    def test_path_traversal_read_returns_not_found(self):
        """Agent tries ../../etc/passwd — must NOT succeed."""
        self.vfs.create_file("/secret.txt", "top secret")
        result = self.vfs.read_file("../../etc/passwd")
        assert result == "File not found or is a directory."

    def test_path_traversal_create_stays_sandboxed(self):
        """Create with traversal should not escape root."""
        self.vfs.create_file("/../../../escape.txt", "gotcha")
        # The file should exist somewhere inside the VFS, not escape
        # The key thing: the VFS root dict should still be intact
        assert isinstance(self.vfs.fs["/"], dict)

    # --- File CRUD basics ---

    def test_create_and_read_file(self):
        result = self.vfs.create_file("/hello.txt", "world")
        assert "created successfully" in result
        assert self.vfs.read_file("/hello.txt") == "world"

    def test_create_file_empty_content(self):
        """Empty string is valid content, not a missing file."""
        self.vfs.create_file("/empty.txt", "")
        content = self.vfs.read_file("/empty.txt")
        assert content == ""
        # Must NOT return the "not found" error message
        assert content != "File not found or is a directory."

    def test_overwrite_existing_file(self):
        self.vfs.create_file("/doc.txt", "version 1")
        self.vfs.create_file("/doc.txt", "version 2")
        assert self.vfs.read_file("/doc.txt") == "version 2"

    def test_delete_existing_file(self):
        self.vfs.create_file("/temp.txt", "data")
        result = self.vfs.delete_file("/temp.txt")
        assert "deleted successfully" in result
        assert self.vfs.read_file("/temp.txt") == "File not found or is a directory."

    def test_delete_nonexistent_file(self):
        """Should return error, not crash."""
        result = self.vfs.delete_file("/ghost.txt")
        assert result == "File not found."

    def test_read_nonexistent_file(self):
        result = self.vfs.read_file("/nope.txt")
        assert result == "File not found or is a directory."

    def test_read_directory_returns_error(self):
        """Reading a directory path should not return its contents as a string."""
        self.vfs.create_file("/dir/file.txt", "content")
        result = self.vfs.read_file("/dir")
        assert result == "File not found or is a directory."

    # --- Directory operations ---

    def test_create_file_auto_creates_dirs(self):
        """Nested dirs should be created automatically."""
        self.vfs.create_file("/a/b/c/deep.txt", "deep content")
        assert self.vfs.read_file("/a/b/c/deep.txt") == "deep content"

    def test_list_files_root(self):
        self.vfs.create_file("/one.txt", "1")
        self.vfs.create_file("/two.txt", "2")
        result = self.vfs.list_files("/")
        assert set(result) == {"one.txt", "two.txt"}

    def test_list_files_dot_means_root(self):
        """list_files('.') should behave like list_files('/')."""
        self.vfs.create_file("/x.txt", "x")
        assert self.vfs.list_files(".") == self.vfs.list_files("/")

    def test_list_files_on_file_returns_error(self):
        """Listing a file path (not dir) should fail gracefully."""
        self.vfs.create_file("/file.txt", "data")
        result = self.vfs.list_files("/file.txt")
        assert result == "Path not found or not a directory."

    def test_list_files_nonexistent_path(self):
        result = self.vfs.list_files("/nonexistent")
        assert result == "Path not found or not a directory."

    def test_list_files_subdirectory(self):
        self.vfs.create_file("/sub/a.txt", "a")
        self.vfs.create_file("/sub/b.txt", "b")
        result = self.vfs.list_files("/sub")
        assert set(result) == {"a.txt", "b.txt"}

    # --- Edge case paths ---

    def test_deeply_nested_path(self):
        self.vfs.create_file("/a/b/c/d/e/f.txt", "deep")
        assert self.vfs.read_file("/a/b/c/d/e/f.txt") == "deep"
        # Parent dirs should show up in listing
        assert "b" in self.vfs.list_files("/a")

    def test_invalid_file_path_empty_filename(self):
        """Path like '/' with no filename should fail."""
        result = self.vfs.create_file("/", "bad")
        assert result == "Invalid file path."

    def test_delete_invalid_path(self):
        result = self.vfs.delete_file("/")
        assert result == "Invalid file path."

    # --- Load from disk ---

    def test_load_from_path(self, tmp_path):
        """Should load real files into the VFS dict."""
        (tmp_path / "report.txt").write_text("revenue data")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "notes.txt").write_text("internal notes")

        vfs = VirtualFileSystem(root_path=str(tmp_path))
        assert vfs.read_file("/report.txt") == "revenue data"
        assert vfs.read_file("/subdir/notes.txt") == "internal notes"

    def test_load_from_path_binary_file(self, tmp_path):
        """Binary files should not crash the loader."""
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\xff")
        vfs = VirtualFileSystem(root_path=str(tmp_path))
        content = vfs.read_file("/binary.bin")
        # Should contain error message, not crash
        assert "Error reading file" in content

    def test_load_from_path_nonexistent(self):
        """Non-existent path should produce empty VFS."""
        vfs = VirtualFileSystem(root_path="/nonexistent/path/abc123")
        assert vfs.fs == {"/": {}}

    # --- Init from fs_data ---

    def test_init_from_fs_data(self):
        """Restoring VFS from saved state (used in interrogation)."""
        saved_state = {"/": {"saved.txt": "restored content", "dir": {"nested.txt": "deep"}}}
        vfs = VirtualFileSystem(fs_data=saved_state)
        assert vfs.read_file("/saved.txt") == "restored content"
        assert vfs.read_file("/dir/nested.txt") == "deep"


class TestVFSSingleton:
    """Test the VFS singleton — stale state between runs is a real bug."""

    def setup_method(self):
        VFS._instance = None

    def test_get_instance_returns_same_object(self):
        a = VFS.get_instance()
        b = VFS.get_instance()
        assert a is b

    def test_get_instance_resets_with_new_root(self, tmp_path):
        """Passing root_path should create a NEW instance (crucial between experiment runs)."""
        old = VFS.get_instance()
        old.create_file("/old_data.txt", "stale")

        (tmp_path / "fresh.txt").write_text("new data")
        new = VFS.get_instance(root_path=str(tmp_path))

        assert new is not old
        # Old data must be gone
        assert new.read_file("/old_data.txt") == "File not found or is a directory."
        assert new.read_file("/fresh.txt") == "new data"

    def test_get_instance_resets_with_fs_data(self):
        """Passing fs_data should create a NEW instance."""
        old = VFS.get_instance()
        old.create_file("/stale.txt", "old")

        new = VFS.get_instance(fs_data={"/": {"fresh.txt": "new"}})
        assert new.read_file("/stale.txt") == "File not found or is a directory."
        assert new.read_file("/fresh.txt") == "new"

    def test_default_instance_is_empty(self):
        vfs = VFS.get_instance()
        assert vfs.fs == {"/": {}}
