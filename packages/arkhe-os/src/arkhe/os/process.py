"""
arkhe.os.process
--------------------
Complete subprocess and process-management utilities.

Design rules
~~~~~~~~~~~~
* ``run()`` is the primary entry point — synchronous, shell-safe, typed.
* ``stream()`` lets callers process stdout line-by-line without buffering.
* ``pipe()`` chains multiple commands via Python, not a shell pipe, so it
  works identically on Windows, macOS, and Linux.
* All methods raise ``subprocess.CalledProcessError`` on non-zero exit when
  ``check=True`` (the default for explicit commands).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, Iterator, List, Optional, Sequence, Union


class ProcessResult:
    """
    Thin wrapper around ``subprocess.CompletedProcess`` with extra helpers.
    """

    __slots__ = ("_cp",)

    def __init__(self, cp: subprocess.CompletedProcess) -> None:
        self._cp = cp

    # Delegates
    @property
    def returncode(self) -> int:
        return self._cp.returncode

    @property
    def stdout(self) -> str:
        return (self._cp.stdout or "").strip()

    @property
    def stderr(self) -> str:
        return (self._cp.stderr or "").strip()

    @property
    def ok(self) -> bool:
        """``True`` when the process exited with code 0."""
        return self._cp.returncode == 0

    @property
    def lines(self) -> List[str]:
        """stdout split into non-empty lines."""
        return [l for l in self.stdout.splitlines() if l]

    def raise_on_error(self) -> "ProcessResult":
        """Raise ``CalledProcessError`` if exit code is non-zero."""
        self._cp.check_returncode()
        return self

    def __bool__(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        return (
            f"<ProcessResult code={self.returncode} "
            f"stdout={self.stdout[:60]!r}>"
        )


class Process:
    """Complete subprocess and process utilities."""

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    @staticmethod
    def run(
        command: Union[str, Sequence[str]],
        *,
        cwd: Optional[str | Path] = None,
        env: Optional[Dict[str, str]] = None,
        extra_env: Optional[Dict[str, str]] = None,
        capture: bool = True,
        check: bool = True,
        shell: Optional[bool] = None,
        timeout: Optional[float] = None,
        input: Optional[str] = None,
    ) -> ProcessResult:
        """
        Run a command and return a :class:`ProcessResult`.

        Parameters
        ----------
        command:
            A shell string (``"ls -la"``) **or** a list of args
            (``["ls", "-la"]``).  When a list is given *shell* defaults to
            ``False``; when a string is given it defaults to ``True``.
        cwd:
            Working directory for the subprocess.
        env:
            Full replacement environment dict.  Use *extra_env* to only
            add/override specific variables on top of the current env.
        extra_env:
            Variables merged on top of ``os.environ``.
        capture:
            Capture stdout/stderr (accessible via ``.stdout`` / ``.stderr``).
        check:
            Raise ``CalledProcessError`` on non-zero exit.
        timeout:
            Kill and raise ``TimeoutExpired`` after *timeout* seconds.
        input:
            Text piped to the process's stdin.
        """
        use_shell = isinstance(command, str) if shell is None else shell

        merged_env: Optional[Dict[str, str]] = None
        if env is not None:
            merged_env = env
        elif extra_env is not None:
            merged_env = {**os.environ, **extra_env}

        cp = subprocess.run(
            command,
            shell=use_shell,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            capture_output=capture,
            text=True,
            check=check,
            timeout=timeout,
            input=input,
        )
        return ProcessResult(cp)

    @staticmethod
    def output(
        command: Union[str, Sequence[str]],
        *,
        cwd: Optional[str | Path] = None,
        extra_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Run *command* and return stripped stdout.  Raises on non-zero exit.
        """
        return Process.run(
            command,
            cwd=cwd,
            extra_env=extra_env,
            capture=True,
            check=True,
            timeout=timeout,
        ).stdout

    @staticmethod
    def ok(
        command: Union[str, Sequence[str]],
        *,
        cwd: Optional[str | Path] = None,
    ) -> bool:
        """
        Return ``True`` if *command* exits with code 0, ``False`` otherwise.
        Never raises.
        """
        try:
            return Process.run(command, cwd=cwd, check=False).ok
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    @staticmethod
    def stream(
        command: Union[str, Sequence[str]],
        *,
        cwd: Optional[str | Path] = None,
        extra_env: Optional[Dict[str, str]] = None,
        shell: Optional[bool] = None,
    ) -> Iterator[str]:
        """
        Yield stdout lines in real time (unbuffered).

        Example::

            for line in Process.stream("pip install -r requirements.txt"):
                print(line)
        """
        use_shell = isinstance(command, str) if shell is None else shell
        merged_env = {**os.environ, **extra_env} if extra_env else None

        with subprocess.Popen(
            command,
            shell=use_shell,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                yield line.rstrip("\r\n")

    # ------------------------------------------------------------------
    # Piping
    # ------------------------------------------------------------------

    @staticmethod
    def pipe(
        *commands: Union[str, Sequence[str]],
        cwd: Optional[str | Path] = None,
    ) -> ProcessResult:
        """
        Run a sequence of commands, piping each stdout into the next stdin.

        Works cross-platform without relying on shell pipe characters.

        Example::

            result = Process.pipe("cat access.log", "grep 404", "wc -l")
            print(result.stdout)  # number of 404 lines
        """
        if not commands:
            raise ValueError("pipe() requires at least one command.")

        procs: List[subprocess.Popen] = []
        for i, cmd in enumerate(commands):
            stdin = procs[i - 1].stdout if i > 0 else None
            use_shell = isinstance(cmd, str)
            p = subprocess.Popen(
                cmd,
                shell=use_shell,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(cwd) if cwd else None,
            )
            procs.append(p)

        # Close intermediate stdout handles so upstream procs get SIGPIPE
        for p in procs[:-1]:
            if p.stdout:
                p.stdout.close()

        stdout, stderr = procs[-1].communicate()
        for p in procs[:-1]:
            p.wait()

        cp = subprocess.CompletedProcess(
            args=commands[-1],
            returncode=procs[-1].returncode,
            stdout=stdout,
            stderr=stderr,
        )
        return ProcessResult(cp)

    # ------------------------------------------------------------------
    # Executable discovery
    # ------------------------------------------------------------------

    @staticmethod
    def which(name: str) -> Optional[str]:
        """Return the absolute path to *name* on ``PATH``, or ``None``."""
        return shutil.which(name)

    @staticmethod
    def is_installed(name: str) -> bool:
        """Return ``True`` if *name* is available on ``PATH``."""
        return shutil.which(name) is not None

    @staticmethod
    def python() -> str:
        """Return the absolute path of the current Python interpreter."""
        return sys.executable

    @staticmethod
    def python_run(
        script: Union[str, Path],
        *args: str,
        cwd: Optional[str | Path] = None,
        capture: bool = True,
    ) -> ProcessResult:
        """
        Run a Python script with the current interpreter.

        Equivalent to ``sys.executable script.py *args``.
        """
        return Process.run(
            [sys.executable, str(script), *args],
            cwd=cwd,
            capture=capture,
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    @staticmethod
    @contextmanager
    def background(
        command: Union[str, Sequence[str]],
        *,
        cwd: Optional[str | Path] = None,
        extra_env: Optional[Dict[str, str]] = None,
        shell: Optional[bool] = None,
    ) -> Generator[subprocess.Popen, None, None]:
        """
        Context manager that starts a background process and guarantees
        termination when the block exits.

        Example::

            with Process.background("python -m http.server 8080") as srv:
                requests.get("http://localhost:8080/")
            # server is terminated here
        """
        use_shell = isinstance(command, str) if shell is None else shell
        merged_env = {**os.environ, **extra_env} if extra_env else None

        proc = subprocess.Popen(
            command,
            shell=use_shell,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
        )
        try:
            yield proc
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


__all__ = ["Process", "ProcessResult"]
