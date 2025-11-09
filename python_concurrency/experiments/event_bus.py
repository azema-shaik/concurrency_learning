#!/usr/bin/env python3
"""
eventbus_no_semaphore.py

EventBus (Temp Alert scenario) WITHOUT using asyncio.Semaphore.

- Per-topic bounded queue
- Per-subscriber bounded queue + spawn `max_concurrency` worker tasks
- Handler timeout + retries + exponential backoff
- Simple in-memory DLQ and stores for demo/tests
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

# ---------------- CONFIG (exact numbers from the scenario) -------------------
TOPIC = "temp.reading"
DLQ_TOPIC = f"{TOPIC}.dlq"
QUEUE_CAPACITY = 10
SUBSCRIBER_QUEUE_CAPACITY = 50
DISPATCHER_WORKERS = 1
HANDLER_TIMEOUT = 2.0        # seconds
MAX_RETRIES = 2              # retry attempts (total attempts = MAX_RETRIES + 1)
BACKOFF_DELAYS = [1.0, 2.0]  # seconds
SHUTDOWN_GRACE = 5.0         # seconds
# ---------------------------------------------------------------------------

Event = Dict[str, Any]
Handler = Callable[[Event], Awaitable[None]]


class QueueFullError(Exception):
    """Raised when a topic queue or subscriber queue is full."""


@dataclass
class Subscription:
    topic: str
    id: str
    unsubscribe_coro: Callable[[], Awaitable[None]]


@dataclass
class _Subscriber:
    id: str
    handler: Handler
    max_concurrency: int
    queue_capacity: int = SUBSCRIBER_QUEUE_CAPACITY
    task_queue: asyncio.Queue = field(init=False)
    worker_tasks: List[asyncio.Task] = field(init=False, default_factory=list)
    once: bool = False

    def __post_init__(self):
        # per-subscriber queue holds events destined to this handler
        self.task_queue = asyncio.Queue(maxsize=self.queue_capacity)


class EventBus:
    def __init__(self):
        self._topics: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[_Subscriber]] = {}
        self._dispatcher_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        # active handler tasks for observability: maps Task -> (topic, subscriber, event)
        self._active_tasks: Dict[asyncio.Task, Tuple[str, _Subscriber, Event]] = {}

        # demo persistence stores
        self.logger_store: List[Event] = []
        self.alarms_store: List[Event] = []
        self.dlq_store: List[Event] = []

    # ---------------- topic & lifecycle management ----------------
    # Creating queues for each topic. Topic can be example for 'notify'. then notify is topic. create a topic.
    def create_topic(self, topic: str, queue_capacity: int = QUEUE_CAPACITY) -> None:
        # check if topic exist in current topic that this event bus is tracking. 
        # if not add and then corresponding .dlq topic.
        # for notify is would be self._topics['notify'] = asyncio.Queue(max_size = QUEUE_CAPACITY)
        # then add  to keep track of its subscribers: self._subscribers['notify'] = []
        if topic not in self._topics:
            self._topics[topic] = asyncio.Queue(maxsize=queue_capacity)
            self._subscribers.setdefault(topic, [])
        if topic + ".dlq" not in self._topics:
            self._topics[topic + ".dlq"] = asyncio.Queue(maxsize=queue_capacity * 2)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self.create_topic(TOPIC)
        self.create_topic(DLQ_TOPIC, queue_capacity=QUEUE_CAPACITY * 2)
        # spawn dispatcher worker(s)
        for _ in range(DISPATCHER_WORKERS):
            t = asyncio.create_task(self._dispatch_loop(TOPIC))
            self._dispatcher_tasks[TOPIC] = t

    async def shutdown(self, grace_period_seconds: float = SHUTDOWN_GRACE) -> None:
        # stop accepting new publishes
        self._running = False

        # stop dispatchers (they will stop dequeuing new events)
        for task in self._dispatcher_tasks.values():
            task.cancel()
        await asyncio.gather(*self._dispatcher_tasks.values(), return_exceptions=True)
        self._dispatcher_tasks.clear()

        # wait for subscriber worker tasks to finish up to grace_period_seconds
        all_workers = []
        for subs in self._subscribers.values():
            for s in subs:
                all_workers.extend(s.worker_tasks)

        if all_workers:
            done, pending = await asyncio.wait(all_workers, timeout=grace_period_seconds)
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        # move remaining queued events to DLQ
        # collect remaining events: from topic queue, from subscriber queues, and any active tasks metadata
        # topic queue
        for topic, q in self._topics.items():
            while not q.empty():
                try:
                    evt = q.get_nowait()
                except asyncio.QueueEmpty:
                    break
                # avoid moving DLQ contents to DLQ again
                if topic.endswith(".dlq"):
                    continue
                self._send_to_dlq(evt, reason="shutdown_topic_remaining")

        # subscriber queues
        for subs in self._subscribers.values():
            for s in subs:
                while not s.task_queue.empty():
                    try:
                        evt = s.task_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    self._send_to_dlq(evt, reason=f"shutdown_subscriber_queue:{s.id}")

        # active tasks -> dlq (if their events are not already DLQed)
        for t, meta in list(self._active_tasks.items()):
            _, _, event = meta
            if not any(e.get("event_id") == event.get("event_id") for e in self.dlq_store):
                self._send_to_dlq(event, reason="shutdown_active_task")

    # ---------------- publish / subscribe ----------------
    async def publish(self, topic: str, event: Event, *, await_handlers: bool = False) -> None:
        if not self._running:
            raise RuntimeError("EventBus not running")
        if topic not in self._topics:
            raise RuntimeError(f"Unknown topic {topic}")
        q = self._topics[topic]
        if q.full():
            raise QueueFullError(f"Topic {topic} queue is full")
        q.put_nowait(event)
        return

    async def subscribe(self, topic: str, handler: Handler, *, max_concurrency: int = 1, queue_capacity: Optional[int] = None, once: bool = False) -> Subscription:
        if topic not in self._topics:
            raise RuntimeError(f"Unknown topic {topic}")
        sid = str(uuid.uuid4())
        sub = _Subscriber(id=sid, handler=handler, max_concurrency=max_concurrency, once=once)
        if queue_capacity is not None:
            sub.task_queue = asyncio.Queue(maxsize=queue_capacity)
        # spawn worker tasks for this subscriber (no semaphores)
        for _ in range(max_concurrency):
            wt = asyncio.create_task(self._subscriber_worker(sub, topic))
            sub.worker_tasks.append(wt)

        self._subscribers.setdefault(topic, []).append(sub)

        async def _unsubscribe():
            # remove subscriber so dispatcher won't enqueue new events to its queue
            lst = self._subscribers.get(topic, [])
            self._subscribers[topic] = [s for s in lst if s.id != sid]
            # then wait for the subscriber's worker tasks to finish processing queued items
            if sub.worker_tasks:
                # signal workers to exit by canceling them after queue drained
                # we'll first allow queue to drain then cancel
                # wait briefly for queue to drain up to a small timeout
                try:
                    await asyncio.wait_for(self._drain_subscriber_queue(sub, timeout=1.0), timeout=1.5)
                except asyncio.TimeoutError:
                    # if still items, cancel workers
                    for t in sub.worker_tasks:
                        t.cancel()
                await asyncio.gather(*sub.worker_tasks, return_exceptions=True)

        return Subscription(topic=topic, id=sid, unsubscribe_coro=_unsubscribe)

    async def _drain_subscriber_queue(self, sub: _Subscriber, timeout: float) -> None:
        # wait until queue is empty or timeout
        start = asyncio.get_event_loop().time()
        while not sub.task_queue.empty():
            if asyncio.get_event_loop().time() - start > timeout:
                raise asyncio.TimeoutError()
            await asyncio.sleep(0.01)

    # ---------------- internal dispatch & handler management ----------------
    async def _dispatch_loop(self, topic: str) -> None:
        q = self._topics[topic]
        try:
            while True:
                event = await q.get()
                subs = list(self._subscribers.get(topic, []))
                for sub in subs:
                    # attempt to enqueue into subscriber queue
                    try:
                        sub.task_queue.put_nowait(event)
                    except asyncio.QueueFull:
                        # subscriber queue full: treat as handler failure for that subscriber,
                        # move to DLQ (or we could drop/raise depending on policy)
                        self._send_to_dlq(event, reason=f"subscriber_queue_full:{sub.id}")
                # continue - dispatcher does not wait for subscriber handlers
        except asyncio.CancelledError:
            return

    # subscriber worker: runs handler(event) with retries for events taken from subscriber.task_queue
    async def _subscriber_worker(self, sub: _Subscriber, topic: str) -> None:
        try:
            while True:
                event = await sub.task_queue.get()
                # create a dedicated task running handler-with-retries for observability
                task = asyncio.create_task(self._run_handler_with_retries(sub, event))
                self._active_tasks[task] = (topic, sub, event)
                # wait for this single task here: worker serializes per worker slot
                try:
                    await task
                finally:
                    # cleanup metadata
                    self._active_tasks.pop(task, None)
                # if the subscription was "once", remove it after first success (best-effort)
                if sub.once:
                    # best-effort removal: if still present, remove
                    lst = self._subscribers.get(topic, [])
                    self._subscribers[topic] = [s for s in lst if s.id != sub.id]
                    # and then exit loop (worker finishes)
                    break
        except asyncio.CancelledError:
            return

    # run handler with timeout + retries; on final failure send event to DLQ
    async def _run_handler_with_retries(self, sub: _Subscriber, event: Event) -> None:
        attempt = 0
        last_exc = None
        while attempt <= MAX_RETRIES:
            try:
                coro = sub.handler(event)
                await asyncio.wait_for(coro, timeout=HANDLER_TIMEOUT)
                return
            except asyncio.TimeoutError as te:
                last_exc = te
                attempt += 1
                if attempt > MAX_RETRIES:
                    break
                await asyncio.sleep(BACKOFF_DELAYS[min(attempt - 1, len(BACKOFF_DELAYS) - 1)])
            except Exception as exc:
                last_exc = exc
                attempt += 1
                if attempt > MAX_RETRIES:
                    break
                await asyncio.sleep(BACKOFF_DELAYS[min(attempt - 1, len(BACKOFF_DELAYS) - 1)])
        # final failure -> DLQ
        self._send_to_dlq(event, reason=f"handler_failed:{sub.id}:{last_exc}")

    # ---------------- DLQ writer ----------------
    def _send_to_dlq(self, event: Event, reason: str) -> None:
        e = dict(event)
        e["_dlq_reason"] = reason
        self.dlq_store.append(e)


# ---------------- Example subscribers (logger & alarm) ----------------
async def logger_handler_factory(bus: EventBus):
    seen = set()
    async def logger(event: Event) -> None:
        eid = event.get("event_id")
        if eid in seen:
            return
        await asyncio.sleep(0.01)  # simulate short IO
        bus.logger_store.append(event.copy())
        seen.add(eid)
    return logger

async def alarm_handler_factory(bus: EventBus, sleep_override: Optional[float] = None):
    seen = set()
    async def alarm(event: Event) -> None:
        eid = event.get("event_id")
        temp = float(event.get("temperature_c", 0.0))
        if sleep_override is not None:
            await asyncio.sleep(sleep_override)
        if temp < 75.0:
            return
        if eid in seen:
            return
        bus.alarms_store.append(event.copy())
        seen.add(eid)
    return alarm

def make_event(eid: str, temp: float, sensor_id: str = "sensor-1", ts: str = "2025-10-13T14:00:00Z") -> Event:
    return {
        "event_id": eid,
        "timestamp_utc": ts,
        "sensor_id": sensor_id,
        "temperature_c": float(temp),
    }

# ---------------- Quick test harness (A-E) ----------------
async def run_tests():
    bus = EventBus()
    await bus.start()

    logger_handler = await logger_handler_factory(bus)
    alarm_handler = await alarm_handler_factory(bus)

    sub_logger = await bus.subscribe(TOPIC, logger_handler, max_concurrency=2)
    sub_alarm = await bus.subscribe(TOPIC, alarm_handler, max_concurrency=1)

    results = {"A": False, "B": False, "C": False, "D": False, "E": False}

    # Test A: low temp
    e1 = make_event("E1", 30.0)
    await bus.publish(TOPIC, e1)
    await asyncio.sleep(0.4)
    results["A"] = any(e.get("event_id") == "E1" for e in bus.logger_store) and not any(e.get("event_id") == "E1" for e in bus.alarms_store)

    # Test B: high temp -> alarm
    e2 = make_event("E2", 80.0)
    await bus.publish(TOPIC, e2)
    await asyncio.sleep(0.6)
    results["B"] = any(e.get("event_id") == "E2" for e in bus.logger_store) and any(e.get("event_id") == "E2" for e in bus.alarms_store)

    # Test C: timeout & retry (make alarm slow)
    # unsubscribe and resubscribe slow alarm
    await sub_alarm.unsubscribe_coro()
    slow_alarm = await alarm_handler_factory(bus, sleep_override=3.0)
    sub_alarm2 = await bus.subscribe(TOPIC, slow_alarm, max_concurrency=1)
    e3 = make_event("E3", 80.0)
    await bus.publish(TOPIC, e3)
    await asyncio.sleep(6.0)
    results["C"] = any(e.get("event_id") == "E3" for e in bus.dlq_store)

    # Test D: queue full - separate bus to reliably fill queue
    bus2 = EventBus()
    await bus2.start()
    # ensure no subscribers so queue won't be drained
    bus2._subscribers[TOPIC] = []
    for i in range(QUEUE_CAPACITY):
        await bus2.publish(TOPIC, make_event(f"Q{i}", 20.0))
    D_ok = False
    try:
        await bus2.publish(TOPIC, make_event("Q_extra", 21.0))
        D_ok = False
    except QueueFullError:
        D_ok = True
    results["D"] = D_ok

    # Test E: shutdown during in-flight (slow logger)
    await sub_logger.unsubscribe_coro()
    async def slow_logger(event):
        await asyncio.sleep(4.0)
        bus.logger_store.append(event.copy())
    sub_logger2 = await bus.subscribe(TOPIC, slow_logger, max_concurrency=1)
    e4 = make_event("E4", 30.0)
    await bus.publish(TOPIC, e4)
    await asyncio.sleep(0.1)
    await bus.shutdown(grace_period_seconds=2.0)
    results["E"] = any(e.get("event_id") == "E4" for e in bus.dlq_store)

    return bus, results

if __name__ == "__main__":
    res = asyncio.run(run_tests())
    bus_obj, test_results = res
    print("Test Results:", test_results)
    print("Logger store:", [e["event_id"] for e in bus_obj.logger_store])
    print("Alarms store:", [e["event_id"] for e in bus_obj.alarms_store])
    print("DLQ store:", [e["event_id"] for e in bus_obj.dlq_store])
