from io import BytesIO

from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig
from domeneshop_mcp.tools_sftp_read import sftp_get_file_metadata, sftp_list_allowed_roots, sftp_read_text_file


class FakeStat:
    filename = "index.php"
    st_size = 17
    st_mode = 33188
    st_mtime = 1_700_000_000


class FakeSftp:
    def stat(self, path):
        return FakeStat()

    def open(self, path, mode):
        return BytesIO(b"<?php echo 'ok';")


def test_list_allowed_roots():
    config = SftpReadConfig(allowed_roots=("/www", "/www/atlas_control"))
    client = SftpReadClient(config, sftp=FakeSftp())
    result = sftp_list_allowed_roots(client)
    assert result["success"] is True
    assert "/www" in result["data"]


def test_metadata_read_allowed_path():
    config = SftpReadConfig(allowed_roots=("/www",))
    client = SftpReadClient(config, sftp=FakeSftp())
    result = sftp_get_file_metadata(client, "/www/index.php")
    assert result["success"] is True
    assert result["data"]["path"] == "/www/index.php"


def test_text_read_includes_hash_and_content():
    config = SftpReadConfig(allowed_roots=("/www",), allowed_text_extensions=frozenset({".php"}))
    client = SftpReadClient(config, sftp=FakeSftp())
    result = sftp_read_text_file(client, "/www/index.php")
    assert result["success"] is True
    assert result["data"]["sha256"]
    assert "<?php" in result["data"]["content"]


def test_text_read_rejects_unapproved_extension():
    config = SftpReadConfig(allowed_roots=("/www",), allowed_text_extensions=frozenset({".php"}))
    client = SftpReadClient(config, sftp=FakeSftp())
    result = sftp_read_text_file(client, "/www/image.png")
    assert result["success"] is False
    assert result["error_class"] == "validation_failed"
