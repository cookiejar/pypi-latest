"""Top-level package for pypi-latest."""

__author__ = "Lukas Heumos"
__email__ = "lukas.heumos@posteo.net"
__version__ = "0.1.0"

import json
import logging
import sys
import urllib.request
from logging import Logger
from subprocess import PIPE, Popen, check_call
from urllib.error import HTTPError, URLError

from pkg_resources import parse_version
from rich import print

from pypi_latest.questionary import custom_questionary

log: Logger = logging.getLogger(__name__)


class PypiLatest:
    """Responsible for checking for newer versions and upgrading it if required."""

    def __init__(self, package_name: str, latest_local_version: str):
        """Constructor for PypiLatest."""
        self.package_name = package_name
        self.latest_local_version = latest_local_version

    def check_upgrade(self) -> None:
        """Checks whether the locally installed version of the package is the latest.

        If not it prompts whether to upgrade and runs the upgrade command if desired.
        """
        if not PypiLatest.check_latest(self):
            if custom_questionary(function="confirm", question="Do you want to upgrade?", default="y"):
                PypiLatest.upgrade(self)

    def check_latest(self) -> bool:
        """Checks whether the locally installed version of the package is the latest available on PyPi.

        Returns:
            True if locally version is the latest or PyPI is inaccessible, False otherwise
        """
        sliced_local_version = (
            self.latest_local_version[:-9]
            if self.latest_local_version.endswith("-SNAPSHOT")
            else self.latest_local_version
        )
        log.debug(f"Latest local {self.package_name} version is: {self.latest_local_version}.")
        log.debug(f"Checking whether a new {self.package_name} version exists on PyPI.")
        try:
            # Retrieve info on latest version
            # Adding nosec (bandit) here, since we have a hardcoded https request
            # It is impossible to access file:// or ftp://
            # See: https://stackoverflow.com/questions/48779202/audit-url-open-for-permitted-schemes-allowing-use-of-file-or-custom-schemes
            req = urllib.request.Request(f"https://pypi.org/pypi/{self.package_name}/json")  # nosec
            with urllib.request.urlopen(req, timeout=1) as response:  # nosec
                contents = response.read()
                data = json.loads(contents)
                latest_pypi_version = data["info"]["version"]
        except (HTTPError, TimeoutError, URLError):
            print(
                f"[bold red]Unable to contact PyPI to check for the latest {self.package_name} version. "
                "Do you have an internet connection?"
            )
            # Returning true by default, since this is not a serious issue
            return True

        if parse_version(sliced_local_version) > parse_version(latest_pypi_version):
            print(
                f"[bold yellow]Installed version {self.latest_local_version} of {self.package_name} is newer than the latest release {latest_pypi_version}!"
                f" You are running a nightly version and features may break!"
            )
        elif parse_version(sliced_local_version) == parse_version(latest_pypi_version):
            return True
        else:
            print(
                f"[bold red]Installed version {self.latest_local_version} of {self.package_name} is outdated. Newest version is {latest_pypi_version}!"
            )
            return False

        return False

    def upgrade(self) -> None:
        """Calls pip as a subprocess with the --upgrade flag to upgrade the package to the latest version."""
        log.debug(f"Attempting to upgrade {self.package_name} via   pip install --upgrade {self.package_name}   .")
        if not PypiLatest.is_pip_accessible():
            sys.exit(1)
        try:
            check_call([sys.executable, "-m", "pip", "install", "--upgrade", self.package_name])
        except Exception as e:
            print(f"[bold red]Unable to upgrade {self.package_name}")
            print(f"[bold red]Exception: {e}")

    @classmethod
    def is_pip_accessible(cls) -> bool:
        """Verifies that pip is accessible and in the PATH.

        Returns:
            True if accessible, False if not
        """
        log.debug("Verifying that pip is accessible.")
        pip_installed = Popen(["pip", "--version"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
        (git_installed_stdout, git_installed_stderr) = pip_installed.communicate()
        if pip_installed.returncode != 0:
            log.debug("Pip was not accessible! Attempted to test via   pip --version   .")
            print("[bold red]Unable to find 'pip' in the PATH. Is it installed?")
            print("[bold red]Run command was [green]'pip --version '")
            return False

        return True
