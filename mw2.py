import asyncio, sys
from .context import ContextCreator

import logging


class MiddleWare():
    def __init__(self, LH, LP, TH, TP):
        self._listener_host = LH
        self._listener_port = LP
        self._target_host = TH
        self._target_port = TP
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
        tr, tw = await asyncio.open_connection(self._target_host, self._target_port)
        await asyncio.gather(self._pump(r, tw), self._pump(tr, w))

    async def _start_server(self):
        server = await asyncio.start_server(self._handle, self._listener_host, self._listener_port)
        async with server: await server.serve_forever()


