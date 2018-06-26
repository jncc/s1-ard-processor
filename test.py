import os
from tempfile import NamedTemporaryFile


fileName = ""

with NamedTemporaryFile(mode='rb+', delete=False) as temp:
    temp.write(os.urandom(20))
    fileName = temp.name


os.remove(fileName)

