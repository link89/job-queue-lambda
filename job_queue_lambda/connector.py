from typing import Optional, Union

from dataclasses import dataclass

import asyncssh
from asyncssh import SSHClientConnection, SSHListener

import asyncio
from logging import getLogger

from .config import SshConfig


logger = getLogger(__name__)


def ensure_str(byte_or_str: Union[bytes, str, None], encoding='utf-8') -> str:
    if byte_or_str is None:
        return ""
    if isinstance(byte_or_str, bytes):
        return byte_or_str.decode(encoding=encoding)
    return byte_or_str  # type: ignore


@dataclass
class CmdResult:
    stdout: str
    stderr: str
    return_code: Optional[int]


class Connector:
    def get_socks_proxy(self):
        raise NotImplementedError()

    async def run(self, cmd: str) -> CmdResult:
        raise NotImplementedError()


class SshConnector(Connector):

    def __init__(self, config: SshConfig):
        self.config = config
        self._connect: Optional[SSHClientConnection] = None
        self._ssh_listener: Optional[SSHListener] = None

    def close(self):
        try:
            self._ssh_listener.close()  # type: ignore
            self._connect.close() # type: ignore
            self._ssh_listener = None
            self._connect = None
        except Exception:
            pass

    async def connect(self):
        if self._connect is not None:
            try:
                # test connection
                await self._connect.run("echo hello")
            except Exception:
                logger.exception("SSH connection failed")
                self.close()
        if self._connect is None:
            self._connect = await asyncssh.connect(
                self.config.host,
                port=self.config.port,
                config=self.config.config_file,
            )
            self._ssh_listener = await self._connect.forward_socks(
                '127.0.0.1', self.config.socks_port)
            await self.run(f"mkdir -p {self.config.tmp_dir}")
        return self._connect

    def get_socks_proxy(self):
        return f"socks5h://127.0.0.1:{self.config.socks_port}"

    async def run(self, cmd: str):
        conn = await self.connect()
        result = await conn.run(cmd)
        return CmdResult(
            stdout=ensure_str(result.stdout),
            stderr=ensure_str(result.stderr),
            return_code=result.exit_status
        )

class LocalConnector(Connector):

    def get_socks_proxy(self):
        return None

    async def run(self, cmd: str):
        result = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        return CmdResult(
            stdout=ensure_str(stdout),
            stderr=ensure_str(stderr),
            return_code=result.returncode
        )

