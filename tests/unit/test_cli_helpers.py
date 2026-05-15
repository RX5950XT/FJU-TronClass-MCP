from __future__ import annotations

from click.exceptions import Exit
import pytest

from fju_tronclass.errors import ClientError, SessionExpiredError


async def _raise_session_expired() -> None:
    raise SessionExpiredError()


async def _raise_client_error() -> None:
    raise ClientError(403, "Forbidden")


def test_run_async_command_converts_session_expired_to_exit() -> None:
    from fju_tronclass.cli._helpers import run_async_command

    with pytest.raises(Exit) as exc_info:
        run_async_command(_raise_session_expired())

    assert exc_info.value.exit_code == 1


def test_run_async_command_converts_domain_errors_to_exit() -> None:
    from fju_tronclass.cli._helpers import run_async_command

    with pytest.raises(Exit) as exc_info:
        run_async_command(_raise_client_error())

    assert exc_info.value.exit_code == 1
