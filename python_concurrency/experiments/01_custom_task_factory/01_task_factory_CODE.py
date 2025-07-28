import asyncio 
from asyncio import tasks as t
from asyncio import futures, coroutines, base_tasks, exceptions
from types import GenericAlias 
import inspect
import contextvars



class Task(futures._PyFuture):  # Inherit Python Task implementation
                                # from a Python Future implementation.

    """A coroutine wrapped in a Future."""
    # An important invariant maintained while a Task not done:
    # _fut_waiter is either None or a Future.  The Future
    # can be either done() or not done().
    # The task can be in any of 3 states:
    #
    # - 1: _fut_waiter is not None and not _fut_waiter.done():
    #      __step() is *not* scheduled and the Task is waiting for _fut_waiter.
    # - 2: (_fut_waiter is None or _fut_waiter.done()) and __step() is scheduled:
    #       the Task is waiting for __step() to be executed.
    # - 3:  _fut_waiter is None and __step() is *not* scheduled:
    #       the Task is currently executing (in __step()).
    #
    # * In state 1, one of the callbacks of __fut_waiter must be __wakeup().
    # * The transition from 1 to 2 happens when _fut_waiter becomes done(),
    #   as it schedules __wakeup() to be called (which calls __step() so
    #   we way that __step() is scheduled).
    # * It transitions from 2 to 3 when __step() is executed, and it clears
    #   _fut_waiter to None.

    # If False, don't log a message if the task is destroyed while its
    # status is still pending
    _log_destroy_pending = True

    def __init__(self, coro, *, loop=None, name=None, context=None,
                 eager_start=False):
        super().__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]
        if not coroutines.iscoroutine(coro):
            # raise after Future.__init__(), attrs are required for __del__
            # prevent logging for pending task in __del__
            self._log_destroy_pending = False
            raise TypeError(f"a coroutine was expected, got {coro!r}")

        if name is None:
            self._name = f'Task-{t._task_name_counter()}'
        else:
            self._name = str(name)

        self._num_cancels_requested = 0
        self._must_cancel = False
        self._fut_waiter = None
        self._coro = coro
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context

        if eager_start and self._loop.is_running():
            self.__eager_start()
        else:
            print(f'\033[38;5;10m[INFO] [in if]\033[0m')
            self._loop.call_soon(self.__step, context=self._context)
            t._register_task(self)

    def __del__(self):
        if self._state == futures._PENDING and self._log_destroy_pending:
            context = {
                'task': self,
                'message': 'Task was destroyed but it is pending!',
            }
            if self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        super().__del__()

    __class_getitem__ = classmethod(GenericAlias)

    def __repr__(self):
        return base_tasks._task_repr(self)

    def get_coro(self):
        return self._coro

    def get_context(self):
        return self._context

    def get_name(self):
        return self._name

    def set_name(self, value):
        self._name = str(value)

    def set_result(self, result):
        raise RuntimeError('Task does not support set_result operation')

    def set_exception(self, exception):
        raise RuntimeError('Task does not support set_exception operation')

    def get_stack(self, *, limit=None):
        """Return the list of stack frames for this task's coroutine.

        If the coroutine is not done, this returns the stack where it is
        suspended.  If the coroutine has completed successfully or was
        cancelled, this returns an empty list.  If the coroutine was
        terminated by an exception, this returns the list of traceback
        frames.

        The frames are always ordered from oldest to newest.

        The optional limit gives the maximum number of frames to
        return; by default all available frames are returned.  Its
        meaning differs depending on whether a stack or a traceback is
        returned: the newest frames of a stack are returned, but the
        oldest frames of a traceback are returned.  (This matches the
        behavior of the traceback module.)

        For reasons beyond our control, only one stack frame is
        returned for a suspended coroutine.
        """
        return base_tasks._task_get_stack(self, limit)

    def print_stack(self, *, limit=None, file=None):
        """Print the stack or traceback for this task's coroutine.

        This produces output similar to that of the traceback module,
        for the frames retrieved by get_stack().  The limit argument
        is passed to get_stack().  The file argument is an I/O stream
        to which the output is written; by default output is written
        to sys.stderr.
        """
        return base_tasks._task_print_stack(self, limit, file)

    def cancel(self, msg=None):
        """Request that this task cancel itself.

        This arranges for a CancelledError to be thrown into the
        wrapped coroutine on the next cycle through the event loop.
        The coroutine then has a chance to clean up or even deny
        the request using try/except/finally.

        Unlike Future.cancel, this does not guarantee that the
        task will be cancelled: the exception might be caught and
        acted upon, delaying cancellation of the task or preventing
        cancellation completely.  The task may also return a value or
        raise a different exception.

        Immediately after this method is called, Task.cancelled() will
        not return True (unless the task was already cancelled).  A
        task will be marked as cancelled when the wrapped coroutine
        terminates with a CancelledError exception (even if cancel()
        was not called).

        This also increases the task's count of cancellation requests.
        """
        self._log_traceback = False
        if self.done():
            return False
        self._num_cancels_requested += 1
        # These two lines are controversial.  See discussion starting at
        # https://github.com/python/cpython/pull/31394#issuecomment-1053545331
        # Also remember that this is duplicated in _asynciomodule.c.
        # if self._num_cancels_requested > 1:
        #     return False
        if self._fut_waiter is not None:
            if self._fut_waiter.cancel(msg=msg):
                # Leave self._fut_waiter; it may be a Task that
                # catches and ignores the cancellation so we may have
                # to cancel it again later.
                return True
        # It must be the case that self.__step is already scheduled.
        self._must_cancel = True
        self._cancel_message = msg
        return True

    def cancelling(self):
        """Return the count of the task's cancellation requests.

        This count is incremented when .cancel() is called
        and may be decremented using .uncancel().
        """
        return self._num_cancels_requested

    def uncancel(self):
        """Decrement the task's count of cancellation requests.

        This should be called by the party that called `cancel()` on the task
        beforehand.

        Returns the remaining number of cancellation requests.
        """
        if self._num_cancels_requested > 0:
            self._num_cancels_requested -= 1
        return self._num_cancels_requested

    def __eager_start(self):
        prev_task = t._swap_current_task(self._loop, self)
        try:
            t._register_eager_task(self)
            try:
                self._context.run(self.__step_run_and_handle_result, None)
            finally:
                t._unregister_eager_task(self)
        finally:
            try:
                curtask = t._swap_current_task(self._loop, prev_task)
                assert curtask is self
            finally:
                if self.done():
                    self._coro = None
                    self = None  # Needed to break cycles when an exception occurs.
                else:
                    t._register_task(self)

    def __step(self, exc=None,*,sent_from = ''):
        print(f'\033[38;5;14m[INFO] [__step] [{exc = !r}], [{sent_from = !r}]\033[0m')
        if self.done():
            raise exceptions.InvalidStateError(
                f'_step(): already done: {self!r}, {exc!r}')
        if self._must_cancel:
            if not isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = False
        self._fut_waiter = None

        t._enter_task(self._loop, self)
        try:
            self.__step_run_and_handle_result(exc)
        finally:
            t._leave_task(self._loop, self)
            self = None  # Needed to break cycles when an exception occurs.

    def __step_run_and_handle_result(self, exc):
        print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result],[{exc = !r}]\033[0m')
        coro = self._coro
        try:
            if exc is None:
                # We use the `send` method directly, because coroutines
                # don't have `__iter__` and `__next__` methods.
                result = coro.send(None)
                print(f'\033[38;5;10m[INFO] [__step_run_and_handle_result] [{result = !r}], [{result._asyncio_future_blocking = !r}]\033[0m')
            else:
                result = coro.throw(exc)
        except StopIteration as exc:
            if self._must_cancel:
                print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [{self._must_cancel = }]\033[0m')
                # Task is cancelled right before coro stops.
                self._must_cancel = False
                super().cancel(msg=self._cancel_message)
            else:
                print(f'\033[38;5;12m[INFO] [__step_run_and_handle_result] [{exc.value = !r}]\033[0m')
                super().set_result(exc.value)
        except exceptions.CancelledError as exc:
            # Save the original exception so we can chain it later.
            self._cancelled_exc = exc
            super().cancel()  # I.e., Future.cancel(self).
        except (KeyboardInterrupt, SystemExit) as exc:
            super().set_exception(exc)
            raise
        except BaseException as exc:
            print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [BaseException = {exc!r}]\033[0m')
            super().set_exception(exc)
        else:
            print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [try-else] [{result = !r }]\033[0m')
            blocking = getattr(result, '_asyncio_future_blocking', None)
            print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [try-else] [{blocking = !r}]\033[0m')
            if blocking is not None:
                # Yielded Future must come from Future.__iter__().
                if futures._get_loop(result) is not self._loop:
                    new_exc = RuntimeError(
                        f'Task {self!r} got Future '
                        f'{result!r} attached to a different loop')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context)
                elif blocking:
                    if result is self:
                        new_exc = RuntimeError(
                            f'Task cannot await on itself: {self!r}')
                        self._loop.call_soon(
                            self.__step, new_exc, context=self._context)
                    else:
                        result._asyncio_future_blocking = False
                        print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [add_done_call_back] [{result =!r}]\033[0m')
                        result.add_done_callback(
                            self.__wakeup, context=self._context)
                        print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [_fut_waiter] [{result =!r}]\033[0m')
                        self._fut_waiter = result
                        print(f'\033[38;5;14m[INFO] [__step_run_and_handle_result] [_fut_waiter] [{self._fut_waiter =!r}]\033[0m')
                        if self._must_cancel:
                            if self._fut_waiter.cancel(
                                    msg=self._cancel_message):
                                self._must_cancel = False
                else:
                    new_exc = RuntimeError(
                        f'yield was used instead of yield from '
                        f'in task {self!r} with {result!r}')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context,from_start = '_step_run_and_handle_result._else_blocking')

            elif result is None:
                # Bare yield relinquishes control for one event loop iteration.
                self._loop.call_soon(self.__step, context=self._context)
            elif inspect.isgenerator(result):
                # Yielding a generator is just wrong.
                new_exc = RuntimeError(
                    f'yield was used instead of yield from for '
                    f'generator in task {self!r} with {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)
            else:
                # Yielding something else is an error.
                new_exc = RuntimeError(f'Task got bad yield: {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)
        finally:
            self = None  # Needed to break cycles when an exception occurs.

    def __wakeup(self, future):
        try:
            future.result()
            print(f'\033[38;5;11m[INFO] [__wakeup] [{future._state = !r}]\033[0m')
        except BaseException as exc:
            # This may also be a cancellation.
            print(f'\033[38;5;11m[INFO] [__wakeup] [{future._state = !r}] [{exc = !r}]\033[0m')
            self.__step(exc,sent_from = '_wakeup._BaseException')
        else:
            # Don't pass the value of `future.result()` explicitly,
            # as `Future.__iter__` and `Future.__await__` don't need it.
            # If we call `_step(value, None)` instead of `_step()`,
            # Python eval loop would use `.send(value)` method call,
            # instead of `__next__()`, which is slower for futures
            # that return non-generator iterators from their `__iter__`.
            self.__step(sent_from  = '_wakeup._else')
        self = None  # Needed to break cycles when an exception occurs.

def task_factory(loop, coro,name = None):
    print(f'\033[38;5;9m[INFO] [LOOP INITIALIZED] [{loop = !r}, {name = !r}]\033[0m')
    return Task(coro = coro, loop = loop, name = None)

async def first():
    print("======== FIRST ===================")
    await asyncio.sleep(.5)
    print('========= SECOND =========================')
    await asyncio.sleep(.10)
    print('=========================== THIRD =================')
    await asyncio.sleep(.10)
    print('========== END ===========')

async def main():
    loop = asyncio.get_event_loop()

    loop.set_task_factory(task_factory)
    await asyncio.gather(first())

asyncio.run(main())