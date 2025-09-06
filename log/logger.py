import logging
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from collections import deque

class Logger(logging.Logger):

    def __init__(self, name, socketio):
        super().__init__(name)
        # self.logger = logging.getLogger(name)
        log_format = '%(message)s'
        handler = logging.StreamHandler()
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.addHandler(handler)

        log_file = f"IBFlask_{str(int(time.time()))}.txt"
        formatter = logging.Formatter('%(message)s')
        handler = TimedRotatingFileHandler(log_file, when='h', interval=1)
        handler.setFormatter(formatter)
        self.addHandler(handler)

        self.setLevel(logging.INFO)

        self.log_messages = deque(maxlen=100)  # Store last 100 log messages
        self.socketio = socketio

    def info(self, msg, *args, **kwargs):
        super().info(msg, args, kwargs)
        self.log_messages.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'INFO',
            'message': f'{msg}'
        })
        self.socketio.emit('log_update', list(self.log_messages))

    def error(self, msg, *args, **kwargs):
        super().info(msg)
        self.log_messages.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'ERROR',
            'message': f'{msg}'
        })
        self.socketio.emit('log_update', list(self.log_messages))

    def clear(self):
        self.log_messages.clear()

