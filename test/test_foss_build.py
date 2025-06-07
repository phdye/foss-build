import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from foss_build.app import (
    STOW_PREFIX_BASE,
    main,
    run_autoconf,
    run_build,
    run_command,
    run_configure,
    run_install,
    run_test,
)


class TestFossBuild(unittest.TestCase):

    @patch("foss_build.app.log")
    @patch("subprocess.Popen")
    def test_run_command(self, mock_popen, mock_log):
        """Test running a command and logging output."""
        mock_process = MagicMock()
        mock_process.stdout = ["output line 1\n", "output line 2\n"]
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        log_dir = Path("/fake/log")

        # Mocking mkdir to avoid PermissionError
        with patch.object(Path, "mkdir"):
            with patch("builtins.open", mock_open()):
                exit_code = run_command(["echo", "Hello"], log_dir)

        self.assertEqual(exit_code, 0)
        # mock_log.assert_called_with("output line 2", log_dir / 'raw')

    @patch("foss_build.app.run_command", autospec=True)
    def test_run_autoconf(self, mock_run_command):
        """Test the autoconf step."""
        mock_run_command.return_value = 0
        log_dir = Path("/fake/log")

        with patch("pathlib.Path.exists", return_value=True):
            exit_code = run_autoconf(log_dir, "/fake/prefix", 4, True)

        self.assertEqual(exit_code, 0)
        mock_run_command.assert_called_once_with(["autoconf"], log_dir)

    @patch("foss_build.app.run_command", autospec=True)
    def test_run_configure(self, mock_run_command):
        """Test the configure step."""
        mock_run_command.return_value = 0
        log_dir = Path("/fake/log")
        exit_code = run_configure(log_dir, "/fake/prefix", 4, True)
        self.assertEqual(exit_code, 0)
        mock_run_command.assert_called_once_with(
            ["./configure", "--prefix=/fake/prefix"], log_dir
        )

    @patch("foss_build.app.run_command", autospec=True)
    def test_run_build(self, mock_run_command):
        """Test the build step."""
        mock_run_command.return_value = 0
        log_dir = Path("/fake/log")
        exit_code = run_build(log_dir, "/fake/prefix", 4, True)
        self.assertEqual(exit_code, 0)
        mock_run_command.assert_called_once_with(["make", "-j4"], log_dir)

    @patch("foss_build.app.run_command", autospec=True)
    def test_run_test(self, mock_run_command):
        """Test the test step."""
        mock_run_command.return_value = 0
        log_dir = Path("/fake/log")
        exit_code = run_test(log_dir, "/fake/prefix", 4, True)
        self.assertEqual(exit_code, 0)
        mock_run_command.assert_called_once_with(["make", "-j4", "test"], log_dir)

    @patch("foss_build.app.run_command", autospec=True)
    def test_run_install(self, mock_run_command):
        """Test the install step."""
        mock_run_command.return_value = 0
        log_dir = Path("/fake/log")
        exit_code = run_install(log_dir, "/fake/prefix", 4, True)
        self.assertEqual(exit_code, 0)
        mock_run_command.assert_called_once_with(
            ["sudo", "make", "-j4", "install"], log_dir
        )

    @patch("foss_build.app.run_steps", autospec=True)
    @patch("pathlib.Path.touch", autospec=True)
    @patch("pathlib.Path.exists", autospec=True)
    @patch("os.getenv", autospec=True)
    @patch("foss_build.app.docopt", autospec=True)
    def test_main(
        self, mock_docopt, mock_getenv, mock_exists, mock_touch, mock_run_steps
    ):
        """Test the main function for handling arguments and environment."""
        mock_getenv.side_effect = lambda var, default=None: {
            "PARALLEL": "4",
            "PREFIX": "/fake/prefix",
        }.get(var, default)
        mock_exists.return_value = False
        mock_run_steps.return_value = None

        mock_docopt.return_value = {
            "--large": True,
            "--no-sudo": False,
            "<command>": [],
        }

        with patch("builtins.open", mock_open()):
            main(argv=["--large"])

        # Check the correct stow path was used
        expected_stow_path = f"{STOW_PREFIX_BASE}/foss-build"
        mock_run_steps.assert_called_with(
            ["autoconf", "configure", "build", "test", "install"],
            expected_stow_path,
            4,
            True,
        )


if __name__ == "__main__":
    unittest.main()
