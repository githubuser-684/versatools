import sys, traceback
import os

class Suppressor():
    """
    Context manager to suppress stdout (or any other stream)
    """
    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exception_type, value, traceback):
        sys.stdout = self.stdout
        if exception_type is not None:
            # Do normal exception handling
            raise Exception(f"Got exception: {exception_type} {value} {traceback}")

    def write(self, x): pass

    def flush(self): pass

class Utils():
    """
    Utility functions
    """
    @staticmethod
    def ensure_directories_exist(directories):
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    @staticmethod
    def ensure_files_exist(files):
        for file in files:
            if not os.path.exists(file):
                with open(file, 'w'):
                    pass