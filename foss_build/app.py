"""
foss-build

USAGE:
  foss-build [options] [commands]

Unattended build and install of FOSS packages which use the standard sequence:
    autoconf, configure, make, make test, make install

Unless commands are present, in which case it runs each command in the
order specified by the user. This is to handle resolving build errors
without having to start over from scratch.

Must be executed in the project source root.

Options:
  --large    Switches install prefix to /opt/stow/<project-name>-<version>.
             If the working directory is the root of an unpacked release
             tar with a release version suffix.  The stow prefix is
             generated using "/opt/stow/$(basename ${PWD})".

             Creates .stow trigger so subsequent runs are stowed automatically.

  --no-sudo  Disables the use of sudo during the installation step.

Commands:
  autoconf   Runs autoconf to generate the configure if configure.ac is present.
  configure  Runs the ./configure script with the specified prefix.
  build      Compiles the source code using make with parallel jobs.
  test       Runs tests to verify the build using make test.
  install    Installs the built software to the specified prefix.
             Installation done using sudo unless `--no-sudo` specified.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

from docopt import docopt

# Constants
DEFAULT_PARALLEL: int = 8
DEFAULT_PREFIX: str = "/usr/local"
STOW_PREFIX_BASE: str = "/opt/stow"

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def log(message: str) -> None:
    """Log a message to the console using the logger."""
    logger.info(message)


def main(argv=sys.argv) -> None:
    """Main entry point for the script."""
    # Parse arguments with docopt
    args = docopt(argv=argv, docstring=__doc__)

    # Check environment variables
    parallel: int = int(os.getenv("PARALLEL", DEFAULT_PARALLEL))
    prefix: str = os.getenv("PREFIX", DEFAULT_PREFIX)

    # Check for .stow and .no-sudo trigger files
    use_stow: bool = args["--large"] or Path(".stow").exists()
    use_sudo: bool = not args["--no-sudo"] and not Path(".no-sudo").exists()

    if use_stow:
        current_dir: Path = Path.cwd()
        project_name: str = current_dir.name
        prefix = f"{STOW_PREFIX_BASE}/{project_name}"
        Path(".stow").touch(exist_ok=True)

    if args["--no-sudo"]:
        Path(".no-sudo").touch(exist_ok=True)

    steps: List[str] = (
        args["commands"]
        if args["commands"]
        else ["autoconf", "configure", "build", "test", "install"]
    )

    run_steps(steps, prefix, parallel, use_sudo)


def run_steps(steps: List[str], prefix: str, parallel: int, use_sudo: bool) -> None:
    """
    Runs the specified build steps in sequence.

    Args:
        steps: A list of steps to execute.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.
    """
    step_functions = {
        "autoconf": run_autoconf,
        "configure": run_configure,
        "build": run_build,
        "test": run_test,
        "install": run_install,
    }

    for index, step in enumerate(steps):
        log_dir: Path = Path(f"./log/{index}.{step}")
        exit_code: int = step_functions[step](log_dir, prefix, parallel, use_sudo)
        if exit_code != 0:
            sys.exit(exit_code)


def filter_output(output: str) -> str:
    """
    Filters the output to remove unwanted content such as ANSI codes and redundant lines.

    Args:
        output: The raw output string to filter.

    Returns:
        The filtered output string.
    """
    output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", output)  # ANSI Escape Codes
    output = re.sub(r"\x1b]0;.*\x07", "", output)  # Xterm Titles
    output = re.sub(
        r"[\x01-\x09\x0B\x0C\x0E-\x1F\x7F]", "", output
    )  # Control Characters
    output = re.sub(r"\n\s*\n", "\n", output)  # Remove redundant new lines
    output = re.sub(r"\n{2,}", "\n", output)  # Ensure no consecutive new lines
    return output


def run_autoconf(log_dir: Path, prefix: str, parallel: int, use_sudo: bool) -> int:
    """
    Runs the autoconf step.

    Args:
        log_dir: Path to the directory where logs will be stored.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.

    Returns:
        The exit code of the autoconf command.
    """
    if Path("configure.ac").exists():
        return run_command(["autoconf"], log_dir)
    return 0


def run_configure(log_dir: Path, prefix: str, parallel: int, use_sudo: bool) -> int:
    """
    Runs the configure step.

    Args:
        log_dir: Path to the directory where logs will be stored.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.

    Returns:
        The exit code of the configure command.
    """
    return run_command(["./configure", f"--prefix={prefix}"], log_dir)


def run_build(log_dir: Path, prefix: str, parallel: int, use_sudo: bool) -> int:
    """
    Runs the build step.

    Args:
        log_dir: Path to the directory where logs will be stored.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.

    Returns:
        The exit code of the build command.
    """
    return run_command(["make", f"-j{parallel}"], log_dir)


def run_test(log_dir: Path, prefix: str, parallel: int, use_sudo: bool) -> int:
    """
    Runs the test step.

    Args:
        log_dir: Path to the directory where logs will be stored.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.

    Returns:
        The exit code of the test command.
    """
    return run_command(["make", f"-j{parallel}", "test"], log_dir)


def run_install(log_dir: Path, prefix: str, parallel: int, use_sudo: bool) -> int:
    """
    Runs the install step.

    Args:
        log_dir: Path to the directory where logs will be stored.
        prefix: The installation prefix.
        parallel: Number of parallel jobs for make.
        use_sudo: Whether to use sudo for installation.

    Returns:
        The exit code of the install command.
    """
    command: List[str] = ["make", f"-j{parallel}", "install"]
    if use_sudo:
        command.insert(0, "sudo")
    return run_command(command, log_dir)


def run_command(command: List[str], log_dir: Path) -> int:
    """
    Runs a command as a subprocess and logs the output.

    Args:
        command: List of command elements to execute.
        log_dir: Path to the directory where logs will be stored.

    Returns:
        The exit code of the command.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    raw_log_file: Path = log_dir / "raw"
    txt_log_file: Path = log_dir / "txt"

    with open(raw_log_file, "w") as raw_log:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            log(line.strip(), raw_log_file)
            raw_log.write(line)

    # Wait for process to finish and capture the exit code
    process.wait()
    exit_code: int = process.returncode

    # Process raw log to txt log
    with open(raw_log_file, "r") as raw, open(txt_log_file, "w") as txt:
        raw_content: str = raw.read()
        txt_content: str = filter_output(raw_content)
        txt.write(txt_content)

    return exit_code


if __name__ == "__main__":
    main(sys.argv)
