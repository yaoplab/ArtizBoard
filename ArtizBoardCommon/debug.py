"""Debug wrapper for Flet UI event handlers.

Usage:
    from ArtizBoardCommon.debug import debug_handler
    btn = ft.Button("OK", on_click=debug_handler(my_handler, "Admin.btn_save"))

When DEBUG=True, logs every handler call, errors, and timing.
When DEBUG=False (or tests pass), logs nothing.
"""
import logging, traceback, time, os

logger = logging.getLogger("artizboard.ui")

# Active en dev, desactive en prod ou quand les tests passent
DEBUG = os.environ.get("ARTIZBOARD_DEBUG", "0") == "1"

def set_debug(enabled: bool):
    global DEBUG
    DEBUG = enabled
    if enabled:
        logger.setLevel(logging.DEBUG)
        logger.info("DEBUG UI active")
    else:
        logger.setLevel(logging.WARNING)

def debug_handler(handler, label: str, context: str = ""):
    """Wraps a Flet event handler with debug logging and crash protection.
    
    Args:
        handler: The original on_click/on_change callback
        label: Human-readable label (e.g., "Admin.catalogue.delete_produit")
        context: Optional extra info
    """
    async def wrapper(e):
        start = time.time()
        if DEBUG:
            logger.debug(f"[UI] {label} | START {context}")
        try:
            result = handler(e)
            if DEBUG:
                elapsed = (time.time() - start) * 1000
                logger.debug(f"[UI] {label} | OK ({elapsed:.0f}ms)")
            return result
        except Exception as ex:
            logger.error(f"[UI] {label} | ERROR: {ex}")
            traceback.print_exc()
            # Try to show error in UI if page is available
            try:
                if hasattr(e, 'page') and e.page:
                    e.page.snack_bar = __import__('flet').SnackBar(
                        __import__('flet').Text(f"Erreur: {ex}"), open=True)
                    e.page.update()
            except:
                pass
    return wrapper


def safe_handler(handler, label: str):
    """Wraps a synchronous Flet handler with try/except only (no debug logs).
    
    Use this for production: catches errors, shows snackbar, never crashes.
    """
    def wrapper(e):
        try:
            return handler(e)
        except Exception as ex:
            logger.error(f"[UI] {label} | ERROR: {ex}")
            traceback.print_exc()
            try:
                ctrl = e.control if hasattr(e, 'control') else None
                page = ctrl.page if ctrl and hasattr(ctrl, 'page') else None
                if page:
                    page.snack_bar = __import__('flet').SnackBar(
                        __import__('flet').Text(f"Erreur: {ex}"), open=True)
                    page.update()
            except:
                pass
    return wrapper
