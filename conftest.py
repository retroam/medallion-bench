"""Pytest configuration for MedallionBench tests."""

from __future__ import annotations

import asyncio
import inspect

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Execute async test functions using an event loop.

    Pytest's core does not natively execute ``async def`` tests. Rather than
    requiring an additional dependency, this hook detects coroutine test
    functions (including those marked with ``@pytest.mark.asyncio``) and runs
    them using ``asyncio.run``. Returning ``True`` signals to pytest that the
    test has been handled so the default implementation is skipped.
    """

    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        asyncio.run(testfunction(**pyfuncitem.funcargs))
        return True

    return None


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Provide a session-scoped event loop fixture for async tests."""

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()
