"""Exposes a `app` variable that can be loaded into WSGI"""
from unlister import create_app

app = create_app()
