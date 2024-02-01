
#----------------------------------------------------------------------------
# PySolUtils
#   some util classes
#
# nram, Feb 3, 2021
#
import datetime
class T:
    ''' return current timestamp '''
    def __str__(self):
        return f'{datetime.datetime.now()}'

#----------------------------------------------------------------------------
# custom exceptions
#
class ArgError (Exception):
    def __init__(self, value):
        message = f"{value}"
        super().__init__(message)

class ServiceError (Exception):
    def __init__(self, value):
        message = f"{value}"
        super().__init__(message)

class GeneralError (Exception):
    def __init__(self, value):
        message = f"{value}"
        super().__init__(message)