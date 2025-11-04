from .mw2 import MiddleWare

mw = MiddleWare()
mw.start("0.0.0.0", "8080", "127.0.0.1", "8081")
