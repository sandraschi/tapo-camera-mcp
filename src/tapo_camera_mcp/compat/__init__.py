"""
Compatibility shims for pytapo dependencies.

This module patches kasa to provide compatibility with pytapo's expectations:
- kasa.transports module (imports from klaptransport)
- AuthenticationError exception alias
"""
import sys


def _patch_kasa():
    """Patch kasa module for pytapo compatibility."""
    try:
        import kasa
        
        # Create kasa.transports module if it doesn't exist
        if not hasattr(kasa, 'transports'):
            from types import ModuleType
            transports_module = ModuleType('kasa.transports')
            
            # Import from klaptransport
            from kasa.klaptransport import KlapTransport, KlapTransportV2
            transports_module.KlapTransport = KlapTransport
            transports_module.KlapTransportV2 = KlapTransportV2
            transports_module.__all__ = ['KlapTransport', 'KlapTransportV2']
            
            # Add to kasa module
            sys.modules['kasa.transports'] = transports_module
            kasa.transports = transports_module
        
        # Add AuthenticationError alias if it doesn't exist
        if not hasattr(kasa.exceptions, 'AuthenticationError'):
            from kasa.exceptions import AuthenticationException
            kasa.exceptions.AuthenticationError = AuthenticationException
            kasa.exceptions.__all__ = getattr(kasa.exceptions, '__all__', []) + ['AuthenticationError']
            
    except ImportError:
        # kasa not installed, skip patching
        pass


# Auto-patch on import
_patch_kasa()
