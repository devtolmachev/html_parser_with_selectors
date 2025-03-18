import sys
from types import TracebackType
from loguru import logger
import traceback

def global_exception_handler(
    exctype: type[BaseException], 
    value: BaseException, 
    tb: TracebackType | None
):
    message = (
        f"Exception {exctype.__name__} not handled.\n"
        f"Stack: {"\n".join(traceback.format_tb(tb))}"
    )
    logger.error(message)

sys.excepthook = global_exception_handler
