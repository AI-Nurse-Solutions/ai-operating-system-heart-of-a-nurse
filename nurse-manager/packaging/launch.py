"""Entry point for the packaged Nurse AI OS app (ADR 0003)."""

import sys
import os
import faulthandler

# Temporary native CI diagnostic, restricted to the synthetic self-test.
diagnose = '--self-test' in sys.argv and os.environ.get('NURSE_AI_OS_STARTUP_DIAGNOSTICS') == '1'
if diagnose:
    faulthandler.dump_traceback_later(3)

from nurse_manager.app import main

try:
    sys.exit(main())
finally:
    if diagnose:
        faulthandler.cancel_dump_traceback_later()
