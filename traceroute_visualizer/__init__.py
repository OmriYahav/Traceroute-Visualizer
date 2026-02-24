"""Traceroute Visualizer package."""

__all__ = ["create_app"]


def create_app():
    from traceroute_visualizer.app import create_app as _create_app

    return _create_app()
