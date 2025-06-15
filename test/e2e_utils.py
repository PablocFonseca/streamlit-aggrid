import contextlib
import logging
import os
import shlex
import socket
import subprocess
import sys
import time
import typing
from contextlib import closing
from tempfile import TemporaryFile

import requests


LOGGER = logging.getLogger(__file__)


def _find_free_port():
    """Find and return a free port on the local machine."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))  # 0 means that the OS chooses a random port
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])  # [1] contains the randomly selected port number


class AsyncSubprocess:
    """A context manager. Wraps subprocess. Popen to capture output safely."""

    def __init__(
        self,
        args: typing.List[str],
        cwd: typing.Optional[str] = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
    ):
        """Initialize an AsyncSubprocess instance.

        Args:
            args (List[str]): List of command-line arguments.
            cwd (str, optional): Current working directory. Defaults to None.
            env (dict, optional): Environment variables. Defaults to None.
        """
        self.args = args
        self.cwd = cwd
        self.env = env
        self._proc = None
        self._stdout_file = None

    def terminate(self) -> typing.Optional[str]:
        """Terminate the process and return its stdout/stderr in a string."""
        if self._proc is not None:
            self._proc.terminate()
            self._proc.wait()
            self._proc = None

        # Read the stdout file and close it
        stdout = None
        if self._stdout_file is not None:
            self._stdout_file.seek(0)
            stdout = self._stdout_file.read()
            self._stdout_file.close()
            self._stdout_file = None

        return stdout

    def __enter__(self) -> "AsyncSubprocess":
        """Start the subprocess when entering the context."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the subprocess and close resources when exiting the context."""
        self.stop()

    def start(self):
        # Start the process and capture its stdout/stderr output to a temp
        # file. We do this instead of using subprocess.PIPE (which causes the
        # Popen object to capture the output to its own internal buffer),
        # because large amounts of output can cause it to deadlock.
        self._stdout_file = TemporaryFile("w+")
        LOGGER.info("Running command: %s", shlex.join(self.args))
        self._proc = subprocess.Popen(
            self.args,
            cwd=self.cwd,
            stdout=self._stdout_file,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ.copy(), **self.env} if self.env else None,
        )

    def stop(self):
        """Terminate the subprocess and close resources."""
        if self._proc is not None:
            self._proc.terminate()
            self._proc = None
        if self._stdout_file is not None:
            self._stdout_file.close()
            self._stdout_file = None


class StreamlitRunner:
    """A context manager for running Streamlit scripts."""

    def __init__(
        self, script_path: os.PathLike, server_port: typing.Optional[int] = None
    ):
        """Initialize a StreamlitRunner instance.

        Args:
            script_path (os.PathLike): Path to the Streamlit script to run.
            server_port (int, optional): Port for the Streamlit server. Defaults to None.
        """
        self._process = None
        self.server_port = server_port
        self.script_path = script_path

    def __enter__(self) -> "StreamlitRunner":
        """Start the Streamlit server when entering the context."""
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        """Stop the Streamlit server and close resources when exiting the context."""
        self.stop()

    def start(self):
        """Start the Streamlit server using the specified script and options."""
        self.server_port = self.server_port or _find_free_port()
        self._process = AsyncSubprocess(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(self.script_path),
                f"--server.port={self.server_port}",
                "--server.headless=true",
                "--browser.gatherUsageStats=false",
                "--global.developmentMode=false",
            ]
        )
        self._process.start()
        if not self.is_server_running():
            self._process.stop()
            raise RuntimeError("Application failed to start")

    def stop(self):
        """Stop the Streamlit server and close resources."""
        self._process.stop()

    def is_server_running(self, timeout: int = 30) -> bool:
        """Check if the Streamlit server is running.

        Args:
            timeout (int, optional): Maximum time to wait for the server to start. Defaults to 30.

        Returns:
            bool: True if the server is running, False otherwise.
        """
        with requests.Session() as http_session:
            start_time = time.time()
            while True:
                with contextlib.suppress(requests.RequestException):
                    response = http_session.get(self.server_url + "/_stcore/health")
                    if response.text == "ok":
                        return True
                time.sleep(3)
                if time.time() - start_time > 60 * timeout:
                    return False

    @property
    def server_url(self) -> str:
        """Get the URL of the Streamlit server."""
        if not self.server_port:
            raise RuntimeError("Unknown server port")
        return f"http://localhost:{self.server_port}"
