# IB API imports
from ibapi.client import EClient

class IBClient(EClient):
    """IB API Client"""

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
        self.wrapper = wrapper
