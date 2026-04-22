import os
import sys
import logging
from PySide6.QtCore import QObject, Signal

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__)).replace('\\utils', '').replace('/utils', '')

class LogSignal(QObject):
    log_msg = Signal(str)

class GUILogHandler(logging.Handler):
    def __init__(self, log_signal):
        super().__init__()
        self.log_signal = log_signal

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.log_msg.emit(msg)

# Global signal instance
gui_log_signal = LogSignal()

def setup_logger():
    app_dir = get_app_dir()
    log_file = os.path.join(app_dir, 'log.txt')
    
    logger = logging.getLogger('MoziOkoshi')
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        logger.handlers.clear()
        
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # GUI Handler
    gh = GUILogHandler(gui_log_signal)
    gh.setLevel(logging.INFO)
    gh.setFormatter(formatter)
    logger.addHandler(gh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()
