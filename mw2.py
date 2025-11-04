import asyncio, sys
from .context import ContextCreator

import logging
#Listen host, listen port, target host, target port
LH, LP, TH, TP = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])


class MiddleWare():
    def __init__(self):
        self._context_creator = ContextCreator()

    ### This will extract just the user prompt from the data
    def _extract_user_prompt(self, data):
        return "placeholder"

    ### This will add the dynamic context to the data
    def _add_context_to_data(self, data, context):
        return "placeholder"

    def start(self):
        asyncio.run(self._start_server())

    async def _pump(self, r, w):
        try:
            while data := await r.read(65536):
                user_prompt = self._extract_user_prompt(data)
                context = self._context_creator.retrieve(user_prompt)
                mod_data = self._add_context_to_data(data, context)
                w.write(mod_data)
                await w.drain()
        finally:
            w.close()

    async def _handle(self, r, w):
        tr, tw = await asyncio.open_connection(TH, TP)
        await asyncio.gather(self._pump(r, tw), self._pump(tr, w))

    async def _start_server(self):
        server = await asyncio.start_server(self._handle, LH, LP)
        async with server: await server.serve_forever()


