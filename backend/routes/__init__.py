"""
Routes package initialization.
This package contains route blueprints for the Crypto Trading Bot API.
"""

from . import api, auth

# Export route blueprints
__all__ = ['api', 'auth']
