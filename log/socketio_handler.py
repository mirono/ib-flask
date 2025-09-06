
import logging

class SocketIOHandler(logging.Handler):
    """A logging handler that emits records with SocketIO."""

    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        asctime = record.__dict__["asctime"]
        msecs = record.__dict__["msecs"]
        levelname = record.__dict__["levelname"]
        module = record.__dict__["module"]
        message = record.__dict__["message"]
        msg = f"{asctime}.{round(msecs):03} [{levelname:<5.5s}]  {module:<18s}  {message}"
        self.socketio.emit("update_message_box", msg, namespace="/printing", broadcast=True)
