import os
import sys

# Add the src directory to sys.path so tests can import the local package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


def pytest_pyfunc_call(pyfuncitem):
    """Run async test functions using asyncio.run."""
    import inspect
    import asyncio

    testobj = pyfuncitem.obj
    if inspect.iscoroutinefunction(testobj):
        asyncio.run(testobj(**pyfuncitem.funcargs))
        return True
