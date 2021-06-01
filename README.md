Insert into app_cfg.py

```
class Debugger():
    def __init__(self):
        pass

    def handler(self, req, queries):
        print("URL %s does %s queries" %( req.url, len(queries)))

from tgext.debug import enable_debug
enable_debug(base_config, Debugger())

```