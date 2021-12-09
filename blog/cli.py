commands = list()

def register(func):
    commands.append(func)
    return func