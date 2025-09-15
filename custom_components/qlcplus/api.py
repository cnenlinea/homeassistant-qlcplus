"""API for QLC+ integration."""

import asyncio
import base64

import websockets

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, LOGGER


class QLCPlusAuthError(Exception):
    """Exception to indicate an authentication error."""


class QLCPlusConnectionError(Exception):
    """Exception to indicate a connection error."""


class QLCPlusAPI:
    """Class to handle communication with QLC+ via WebSocket."""

    def __init__(
        self,
        host,
        port=DEFAULT_PORT,
        username=None,
        password=None,
        timeout=DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API with connection parameters."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._ws = None
        self._timeout = timeout

    async def connect(self) -> None:
        """Establish a WebSocket connection to the QLC+ server."""
        url = f"ws://{self._host}:{self._port}/qlcplusWS"
        headers = {}

        if self._username and self._password:
            credentials = f"{self._username}:{self._password}"
            encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
                "utf-8"
            )
            headers["Authorization"] = f"Basic {encoded_credentials}"

        try:
            self._ws = await websockets.connect(url, extra_headers=headers)
            LOGGER.debug("Connected to QLC+ at %s", url)
        except websockets.exceptions.InvalidStatus as exc:
            if exc.response.status_code == 401:
                LOGGER.error(
                    "Authentication failed when connecting to QLC+ at %s", url)
                raise QLCPlusAuthError("Invalid username or password") from exc
            LOGGER.error("Failed to connect to QLC+ at %s: %s", url, exc)
            raise QLCPlusConnectionError(
                f"Connection failed with status code {exc.status_code}"
            ) from exc
        except ConnectionRefusedError as exc:
            LOGGER.error(
                "Connection refused when connecting to QLC+ at %s", url)
            raise QLCPlusConnectionError("Connection refused") from exc

    async def send_command_and_wait_for_response(
        self, command: str, is_retry=False
    ) -> str:
        """Send a command to the QLC+ server and return the response."""
        if not self._ws:
            await self.connect()

        try:
            async with asyncio.timeout(self._timeout):
                await self._ws.send(command)
                command_prefix = "|".join(command.split("|")[:2])
                while True:
                    response = await self._ws.recv()
                    if response.startswith(command_prefix):
                        break
                LOGGER.debug(
                    "Sent command: %s, received response: %s", command, response
                )
                return response
        except TimeoutError as exc:
            LOGGER.error("Timed out waiting for response from QLC+")
            raise QLCPlusConnectionError(
                "Timed out waiting for response") from exc
        except websockets.exceptions.ConnectionClosed:
            self._ws = None
            if not is_retry:
                return await self.send_command_and_wait_for_response(
                    command, is_retry=True
                )
            raise

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            LOGGER.debug("Disconnected from QLC+")

    async def get_list_of_widgets(self) -> dict[str, str]:
        """Retrieve the list of widgets from QLC+."""
        command = "QLC+API|getWidgetsList"
        response = await self.send_command_and_wait_for_response(command)

        widgets = {}

        response_parts = response.split("|")
        for i in range(2, len(response_parts), 2):
            try:
                widget_id = response_parts[i]
                widget_name = response_parts[i + 1]
                widgets[widget_id] = widget_name
            except (IndexError, ValueError):
                LOGGER.warning(
                    "Failed to parse widget information from response: %s", response
                )
                continue

        return widgets

    async def get_widget_status(self, widget_id: str) -> str:
        """Retrieve the status of a specific widget by its ID."""
        command = f"QLC+API|getWidgetStatus|{widget_id}"
        response = await self.send_command_and_wait_for_response(command)

        response_parts = response.split("|")

        return response_parts[2]

    async def set_widget_value(
        self, widget_id: str, value: int, is_retry: bool = False
    ) -> None:
        """Set the value of a specific widget by its ID."""
        if not self._ws:
            await self.connect()

        command = f"{widget_id}|{value}"
        try:
            await self._ws.send(command)
        except websockets.exceptions.ConnectionClosed:
            self._ws = None
            if not is_retry:
                return await self.set_widget_value(widget_id, value, is_retry=True)
            raise

    async def set_gm_value(
        self, value: int, is_retry: bool = False
    ) -> None:
        """Set the value of the GM slider"""
        if not self._ws:
            await self.connect()

        command = f"GM_VALUE|{value}"
        try:
            await self._ws.send(command)
        except websockets.exceptions.ConnectionClosed:
            self._ws = None
            if not is_retry:
                return await self.set_widget_value(widget_id, value, is_retry=True)
            raise

    async def reset_simple_desk(self, is_retry: bool = False) -> None:
        """Resets Simple Desk value."""
        if not self._ws:
            await self.connect()
        command = "QLC+API|sdResetUniverse|1"
        try:
            await self._ws.send(command)
        except websockets.exceptions.ConnectionClosed:
            self._ws = None
            if not is_retry:
                return await self.reset_simple_desk(is_retry=True)
            raise
