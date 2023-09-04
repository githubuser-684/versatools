import sys, traceback
import os
import functools

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
    
    @staticmethod
    def retry_on_exception(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Retry executing function x times until there's no exception
            """
            retries = 3
            err = None
            for _ in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    err = str(e)
            else:
                raise Exception(f"Error {err} while running {func.__name__}. Tried {retries} times")
        return wrapper
    
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