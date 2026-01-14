"""
Compatibility shims for pytapo dependencies.

This module patches kasa to provide compatibility with pytapo's expectations:
- kasa.transports module (imports from klaptransport)
- AuthenticationError exception alias
- TPLinkSmartHomeProtocol (deprecated/removed in newer kasa versions)
"""
import sys


def _patch_kasa():
    """Patch kasa module for pytapo compatibility at sys.modules level."""
    # Create kasa.transports module in sys.modules BEFORE any imports
    if 'kasa.transports' not in sys.modules:
        from types import ModuleType
        transports_module = ModuleType('kasa.transports')

        # Try to import from klaptransport, but don't fail if not available
        try:
            import kasa.klaptransport
            transports_module.KlapTransport = kasa.klaptransport.KlapTransport
            transports_module.KlapTransportV2 = kasa.klaptransport.KlapTransportV2
        except (ImportError, AttributeError):
            # Create dummy classes if klaptransport doesn't exist
            class DummyTransport:
                pass
            transports_module.KlapTransport = DummyTransport
            transports_module.KlapTransportV2 = DummyTransport

        transports_module.__all__ = ['KlapTransport', 'KlapTransportV2']

        # Add to sys.modules BEFORE any pytapo imports
        sys.modules['kasa.transports'] = transports_module

    # Patch TPLinkSmartHomeProtocol in kasa.protocol if it's missing
    try:
        import kasa.protocol
        if not hasattr(kasa.protocol, 'TPLinkSmartHomeProtocol'):
            # Create a compatibility class that inherits from BaseProtocol
            class TPLinkSmartHomeProtocol(kasa.protocol.BaseProtocol):
                """Compatibility shim for deprecated TPLinkSmartHomeProtocol."""
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

            # Add to both the module and sys.modules
            kasa.protocol.TPLinkSmartHomeProtocol = TPLinkSmartHomeProtocol
            if 'kasa.protocol' in sys.modules:
                sys.modules['kasa.protocol'].TPLinkSmartHomeProtocol = TPLinkSmartHomeProtocol
    except ImportError:
        pass

    # Also patch kasa.exceptions if kasa is available
    try:
        import kasa.exceptions
        if not hasattr(kasa.exceptions, 'AuthenticationError'):
            kasa.exceptions.AuthenticationError = kasa.exceptions.AuthenticationException
    except ImportError:
        pass


# Patch BEFORE any other imports in this module
_patch_kasa()
