"""
Central listing of all cli commands installed in different applications.

Author: Valtteri Rajalainen
"""


commands = list()

def register(func):
    commands.append(func)
    return func
