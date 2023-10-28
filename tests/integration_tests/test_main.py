import re
import subprocess
from pathlib import Path

import pytest

from jodo import main
from jodo.db import InstanceExistsError


class TestMain:
    """Test jodo/main.py."""

    name = "jodo-test-container"

    @pytest.fixture(scope="class")
    def _instance(self):
        """Create an instance for use in other tests."""
        assert "jodo_test_container" not in subprocess.check_output(
            ["lxc", "list"],
            universal_newlines=True,
        )
        main.launch(
            cloud="lxd_container",
            name=self.name,
            image="jammy",
            userdata="#cloud-config\nbootcmd:\n - echo 'hi' > /var/tmp/hi",
        )
        yield
        main.delete(self.name)

    def test_no_duplicates(self, _instance) -> None:
        """Test no duplicates."""
        with pytest.raises(InstanceExistsError):
            main.launch(cloud="lxd_container", name=self.name, image="jammy")
        assert "\n".join(main.list_instances()).count(self.name) == 1

    def test_list(self, _instance) -> None:
        """Test list_instances."""
        instances = "\n".join(main.list_instances())
        assert re.search(rf"{self.name}\s*lxd_container", instances)

    def test_execute(self, _instance) -> None:
        """Test execute."""
        assert "hi" in main.execute(self.name, command="cat /var/tmp/hi")

    def test_push(self, _instance, tmp_path: Path) -> None:
        """Test push."""
        local_tmp = tmp_path / "push.txt"
        local_tmp.write_text("push data")
        main.push(self.name, source=str(local_tmp), destination="/tmp/push.txt")
        assert "push data" in main.execute(self.name, "cat /tmp/push.txt")

    def test_pull(self, _instance, tmp_path: Path) -> None:
        """Test pull"""
        local_tmp = tmp_path / "pull.txt"
        main.execute(self.name, "echo 'pull data' > /tmp/pull.txt")
        main.pull(self.name, "/tmp/pull.txt", str(local_tmp))
        assert "pull data" in local_tmp.read_text()
