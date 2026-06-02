"""
Streamlit Stub for Vercel Serverless Environment

When running on Vercel, streamlit is not installed.
This module provides a no-op stub so that `import streamlit as st` 
doesn't crash in modules shared between Streamlit and FastAPI.
"""
import os
import sys


class _NoOpSessionState(dict):
    """Fake session_state that acts like an empty dict."""
    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        self[name] = value


class _StreamlitStub:
    """Minimal stub that silently swallows all st.* calls."""
    secrets = {}
    session_state = _NoOpSessionState()
    _is_running_with_streamlit = False

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def spinner(self, *args, **kwargs):
        """Context manager stub."""
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()

    def cache_data(self, *args, **kwargs):
        """Decorator stub — just returns the original function."""
        def decorator(func):
            return func
        # Handle both @st.cache_data and @st.cache_data(...)
        if args and callable(args[0]):
            return args[0]
        return decorator

    def stop(self):
        pass

    def __getattr__(self, name):
        """Catch-all for any other st.* calls."""
        def noop(*args, **kwargs):
            pass
        return noop


# Only install the stub if streamlit is not actually installed
if os.getenv("VERCEL"):
    sys.modules["streamlit"] = _StreamlitStub()
