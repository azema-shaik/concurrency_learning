import asyncio 
import logging
from asyncio import tasks as t
from asyncio import futures, coroutines, base_tasks, exceptions
from types import GenericAlias 
import inspect
import contextvars
import pathlib

from .logger import LogColors, get_logger


logger = None





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
        logger.info({"msg": "__init__ initalized"})
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
        self._fut_count = 0
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context

        if eager_start and self._loop.is_running():
            self.__eager_start()
        else:
            logger.info({"msg": 'self.__step scheduled on EVENT_LOOP in __init__','vars': {'task_name': self._name,
                                                        'scheduler_type':'call_soon'}})
            self._loop.call_soon(self.__step, None, '__init__',context=self._context)
            logger.info({"msg": "__init__ after scheduling __step on EVENT_LOOP using loop.call_soon",
                         "vars":{"task_name":self._name,'scheduler_type':'call_soon'}})
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

    def __step(self, exc=None,sent_from = ''):
        logger.info({"msg": 'Entered self.__step',"method_signature": "__step(self, exc = None)", "vars": {"task_name" 
                                                            : self._name,  "exc" : repr(exc), "sent_from": repr(sent_from)}})
        if self.done():
            logger.error({"msg": f'task_name = {self._name} is already done so raising InvalidStateError','vars': {"task_name": self._name}})
            raise exceptions.InvalidStateError(
                f'_step(): already done: {self!r}, {exc!r}')
        if self._must_cancel:
            if not isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = False
        logger.info({"msg": "will initalized self._fut_waiter value",'vars': {"task_name": self._name}})
        self._fut_waiter = None
        logger.info({"msg": "initalized self._fut_waiter to None",'vars': {"task_name": self._name}})


        t._enter_task(self._loop, self)
        try:
            logger.info({"msg": "`try` of try-finally in `self.__step`. Call to __step_run_and_handle_request in next line.",'vars': {"task_name": self._name}})
            self.__step_run_and_handle_result(exc)
            logger.info({"msg": "`try` of try-finally in `self.__step`. After __step_run_and_handle_result",'vars': {"task_name": self._name}})
        except BaseException as e:
            logger.error({"msg": 'try-finally in `self.__step` exception encountered','vars': {"exc_caught": repr(e),"task_name": self._name}})
            raise e
        finally:
            logger.info({"msg": "`finally` of try-finally in `self.__step`. Call to _leave_task next and then set self to None",'vars': {"task_name": self._name}})
            t._leave_task(self._loop, self)
            task_name = self._name
            self = None  # Needed to break cycles when an exception occurs.
            logger.info({"msg": f"`finally` of try-finally in `self.__step`.{task_name} set to none","vars": {"task_name": task_name}})

    def __step_run_and_handle_result(self, exc):
        logger.info({"msg": "__step_run_and_handle_request entered","method_signature":"__step_run_and_handle_result(self, exc)",
               "vars": {"task_name": self._name, "exc": repr(exc)}})
        coro = self._coro
        try:
            if exc is None:
                # We use the `send` method directly, because coroutines
                # don't have `__iter__` and `__next__` methods.
                logger.info({"msg":"`__step_run_and_hanle_result` main try-except exc is None so `coro.send()` in next line."
                            ,'vars': {"task_name": self._name}})
                result = coro.send(None)
                logger.info({"msg:": "__step_run_and_handle_result main try-except after `coro.send()`",
                       "vars": {"result": repr(result), "result._asyncio_future_blocking": getattr(result,'_asyncio_future_blocking',"NOT FOUND")}
                                ,'vars': {"task_name": self._name}})
            else:
                logger.info({"msg": "exc is not None. coro.throw(exc) next", 'vars': {"exc":repr(exc)
                            ,'vars': {"task_name": self._name}}})
                result = coro.throw(exc)
                logger.info({"msg": "exc is not None. coro.throw(exc) next", 'vars': {"exc":repr(exc)
                            ,"task_name": self._name}})
        except StopIteration as exc:
            logger.info({"msg":"StopIteration exception encountered.","vars":{"task_name": self._name,'future_name': "NO_AWAITABLE"}})
            if self._must_cancel:
                logger.info({"msg": "__step_run_and_handle_result StopIteration and self._must_cancel is True",
                             'vars': {"task_name": self._name,'future_name':'NO_AWAITABLE'}})
                # Task is cancelled right before coro stops.
                self._must_cancel = False
                super().cancel(msg=self._cancel_message)
                logger.info({"msg": "called super().cancel()",'vars': {"task_name": self._name,'future_name':'NO_AWAITABLE'}})
            else:
                logger.info({"msg": "__step_run_and_handle_result StopIteration encountered but the task is not cancelled."
                             ,'vars': {"task_name": self._name, "exc.value": repr(exc.value)}})
                super().set_result(exc.value)
                logger.info({"msg": "super().set_result(exc.value)",'vars': {"task_name": self._name}})
        except exceptions.CancelledError as exc:
            # Save the original exception so we can chain it later.
            self._cancelled_exc = exc
            super().cancel()  # I.e., Future.cancel(self).
        except (KeyboardInterrupt, SystemExit) as exc:
            super().set_exception(exc)
            raise
        except BaseException as exc:
            logger.info({"msg": "BaseExcpetion encountered. And call super().set_exception(exc)"
                         ,'vars': {"task_name": self._name, "exception": repr(exc)}})
            super().set_exception(exc)
        else:
            if result is not None:
                self._fut_count += 1
                result._fut_name = f'{self._name}: name: {self._fut_count}'
            logger.info({"msg": "try-else in __step_run_and_handle_result" ,'vars': {"task_name": self._name, "future_name": getattr(result,'_fut_name',None), 
                                "result": repr(result), "is_asyncio_future_blocking": f'{getattr(result,"_asyncio_future_blocking", None)= !r}'}})
            blocking = getattr(result, '_asyncio_future_blocking', None)
            logger.info({"msg":"is_future blocking",'vars': {"task_name": self._name, "future_name": getattr(result,'_fut_name',None),'is_future_blocking': blocking}})
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
                        logger.info({"msg": "scheduling on EVENT_LOOP callback to fututre.add_done_call_back",
                                     'vars': {"task_name": self._name, "future_name": getattr(result,'_fut_name',None),
                                            'future_state':result._state,'result': repr(result),'scheduler_type':'call_soon'}})
                        result.add_done_callback(
                            self.__wakeup, context=self._context)
                        logger.info({"msg" : "After scheduling callbacks to fut. self._future_wait = result",
                                     'vars': {"task_name": self._name, "future_name": getattr(result,'_fut_name',None),
                                            "result": str(result),'self._fut_waiter': self._fut_waiter,'future_state':result._state,
                                            "future_callbacks_list(fut._callbacks)": [(fn.__name__,fn.__class__.__name__) 
                                                                                      for fn,_ in result._callbacks]}})
                        self._fut_waiter = result
                        logger.info({"msg":"self._fut_waiter set to result",
                                     'vars': {"task_name": self._name, "future_name": getattr(result,'_fut_name',None),'future_state':result._state,
                                        'self._fut_waiter': repr(result)}})
                        
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
                logger.info({"msg": "result is None. Scheduling on EVENT_LOOP self.__step",'vars': {
                    "task_name": self._name, "future_name": getattr(result,'_fut_name',"No future"),'scheduler_type':'call_soon'}})
                self._loop.call_soon(self.__step, None,'__step_run_and_handle_result',context=self._context)
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
            logger.info({"msg": "self finally set to None",'vars': {"task_name": self._name}})
            self = None  # Needed to break cycles when an exception occurs.


    def __wakeup(self, future):
        logger.info({"msg": '__wakeup entered','vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None),
                                            'future_state': future._state}})
        try:
            logger.info({"msg": "will call future.result()",'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None)}})
            future.result()
            logger.info({'msg':'__wakeup after future.result()',
                   'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None),'future._state':future._state}})
        except BaseException as exc:
            # This may also be a cancellation.
            logger.error({"msg":"__wakeup error when future.result().calling __step with exc",'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None),
                                                                    'exc': repr(exc)}})
            self.__step(exc,sent_from = '_wakeup._BaseException')
            logger.info({"msg": "after sending __step with exception",
                         'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None)},'future_state':future._state,'exc': repr(exc)})
        else:
            # Don't pass the value of `future.result()` explicitly,
            # as `Future.__iter__` and `Future.__await__` don't need it.
            # If we call `_step(value, None)` instead of `_step()`,
            # Python eval loop would use `.send(value)` method call,
            # instead of `__next__()`, which is slower for futures
            # that return non-generator iterators from their `__iter__`.
            logger.info({'msg': f'__wakeup faced no exception when it called future.result()({future._fut_name}). calling again __step with no exc. I guess StopIteration will be raised',
                         'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None),
                                  'future._result': future._result}})
            self.__step(sent_from  = '_wakeup._else')
        logger.info({"msg": "end of __wakeup. set self = None",'vars': {"task_name": self._name, "future_name": getattr(future,'_fut_name',None)}})
        self = None  # Needed to break cycles when an exception occurs.
        

def task_factory(loop, coro, name = None,prefix='async'):
    
    name = f'{prefix}-'.upper()+ (name or f'Custom-task-{f'Task-{t._task_name_counter()}'}')
    logger.info({"msg": "initalizing task", "vars": {"loop": repr(loop), 
                            "coro": repr(coro), 'task_name': name}})
    
    return Task(coro = coro, loop = loop, name = name)



def init_logger(log:logging.Logger):
    global logger
    logger = log
    hdlr,   = filter(lambda hdlr: not isinstance(hdlr,logging.FileHandler), logger.handlers)
    hdlr.formatter._colors = {
                                    "__init__": LogColors.PINK,
                                    "__wakeup": LogColors.YELLOW, "__step": LogColors.RED,
                                    "__step_run_and_handle_result": LogColors.GREEN
    }
    print(hdlr.formatter,hdlr,logger.handlers)
    
    

