# Understanding **Asyncio**

## <u>Understanding `asyncio.Futures`</u>

    ### <u>Operations happening in `asyncio.Futures.__init__`</u>
    - Signature: `__init__(self,*,loop = None)`
    - Initializes following:
        - `self._loop` -> events.get_event_loop() if loop is not None else loop
        -  `self._callbacks` = []

    ### <u>Operations happening in `asyncio.Futures.__scheduled_callbacks`</u>
    - Signature `__scheduled_callbacks(self)`
    - Operations happening:
        - makes a copy of `self._callbacks` -> `callbacks = self._callbacks[:] `
        - if callbacks empty then exits the `self.__scheduled_callbacks` method
        - else:
            - iterates over `callbacks` and scheduleds on event loop using `_loop.call_soon(callback,self, ctx)

    ### <u></u> 

