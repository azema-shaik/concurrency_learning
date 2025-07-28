# Understanding **Asyncio**

## <u>Understanding `asyncio.Future`</u>

### <u>Operations happening in `asyncio.Future.__init__`</u>
- Signature: `__init__(self,*,loop = None)`
- Initializes following:
    - `self._loop` -> events.get_event_loop() if loop is not None else loop
    -  `self._callbacks` = []

### <u>Operations happening in `asyncio.Future.__scheduled_callbacks`</u>
- Signature `__scheduled_callbacks(self)`
- Operations happening:
    - makes a copy of `self._callbacks` -> `callbacks = self._callbacks[:] `
    - **IF** callbacks empty then exits the `self.__scheduled_callbacks` method
    - **ELSE**:
        - iterates over `callbacks` and scheduleds on event loop using `_loop.call_soon(callback,self, ctx)

### <u>Operations happenig in `asyncio.Future.set_result`</u>
- Signature: `set_result(self, result)`
- Operation happening:
    - Checks **IF** `._state!=PENDING`:
        - <span style="color:red">**raise** `InvalidStateError()`</span>
    - **ELSE**:
        - sets `self._result = result`
        - sets `self._state = _FINISHED`
        - <span style="color:pink">SCHEDULES</span> `.__scheduled_callbacks()`

### <u>Operations happening in `asyncio.Future.set_exception`</u>
- Signature: `set_exception(self, exception)`
- Operations happening:
    - Checks **IF** `._state!=PENDING`:
        - <span style="color:red">**raise** `InvalidStateError()`</span>
    - **IF** exception is of type `StopIteration`:
        - <span style="color:red">**raise** `TypeError("StopIteration interacts badly with generators and cannot be raised in futures")`</span>
    - **ELSE**:
        - sets `self._exception = exception`
        - sets `._state = _FINISHED`
        - sets `self._exception_tb = exception.__traceback__`
        - <span style="color:pink">SCHEDULES</span> `.__scheduled_callbacks()`

### <u>Operations happening in `asyncio.Future.cancel`</u>
- Signature: `cancel(self,msg = None)`
- Operations happening:
    - Checks **IF** `self._state != _PENDING`:
        - returns `FALSE`
    - **ELSE**:
        - sets `self._state = _CANCELLED`
        - sets `self._cancel_message = msg`
        - <span style="color:pink">SCHEDULES</span> `.__scheduled_callbacks()`
        - returns `TRUE`

### <u>Operations happening in `asyncio.Future.result`</u>
- Signature: `result(self)`
- Operations happening:
    - **IF** `self._state == CANCELLED`:
        - <span style="color:red">raises `CancelledError()`</span>
    - **ELIF** `self._state != FINISHED`:
        - <span style="color:red">raises `InvalidStateError()`</span>
    - **ELSE**:
        - return `self._result`


### <u>Operations happening in `asyncio.Future.add_done_callbacks`</u>
- Signature: `add_done_callbacks(self,fn,*,context = None)`
- Operations happening:
    - **IF** `self._state != PENDING`:
        - <span style="color:pink">SCHEDULES</span> `._loop.call_soon(fn,context = context)`
    - **ELSE**:
        - appends the `fn` to `self._callbacks`


### <u>Operations happening in `asyncio.Future.remove_done_callbacks`</u>
- Signature: `remove_done_callback(self, function)`
- Operations happening:
    - remove `function` from `self._callbacks`

### <u>Operations happening in `asyncio.Future.__await__`</u>
- Signature: `__await__(self)`:
- Operations happening:
    - **IF** `not self.done()`:
        - `self._asyncio_future_blocking = True
        - yield self
    - **IF** `not self.done()`:
        - <font color="red">raises `RuntimeError("await wasn't used with future")`</font>
    - return `self.result()`

### <u>`__iter__ == __await__`</u>
