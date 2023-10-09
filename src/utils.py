import sys
import os
import functools

class Utils():
    """
    Utility functions
    """
    @staticmethod
    def ensure_directories_exist(directories):
        """
        Creates directories if they don't exist
        """
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    @staticmethod
    def ensure_files_exist(files):
        """
        Creates files if they don't exist
        """
        for file in files:
            if not os.path.exists(file):
                with open(file, 'w'):
                    pass

    @staticmethod
    def clear_line(line: str) -> str:
        """
        Clears a line from spaces, tabs and newlines
        """
        return line.replace("\n", "").replace(" ", "").replace("\t", "")

    @staticmethod
    def retry_on_exception(retries = 3):
        """
        Decorator to retry executing a function x times until there's no exception
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                """
                Retry executing function x times until there's no exception
                """
                err = None
                for _ in range(retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        err = str(e)
                        if "Expecting value: line" in err:
                            err = "JSON decode error. Cookie is invalid OR Rate limit"
                else:
                    raise Exception(f"Error {err}. Tried running {func.__name__} {retries} times")
            return wrapper
        return decorator

class Suppressor():
    """
    Context manager to suppress stdout (or any other stream)
    """
    def __enter__(self):
        # pylint: disable =attribute-defined-outside-init
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exception_type, value, traceback):
        sys.stdout = self.stdout
        if exception_type is not None:
            # Do normal exception handling
            raise Exception(f"Got exception: {exception_type} {value} {traceback}")

    def write(self, x):
        """
        Suppresses the output
        """

    def flush(self):
        """
        Suppresses the output
        """
