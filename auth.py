import os
import json
from glob import glob

class Auth:
    _instance_ = None
    _initialized_ = False
    
    users = []
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_
    
    def __init__(self):
        if not self._initialized_:
            self._initialized_ = True
            
    def read_tokens(self):
        """
        Reads tokens from the tokens folder. File name format: tokens-[phone number].json
        The json structure:
        """
        token_files = glob("tokens-*.json")
        self.users = []
        
        
        