import pytest
import time
import threading
from arkhe.promise import Promise, PromiseError, PromiseTimeoutError, PromiseCancelledError, PromiseAllError, PromiseAnyError

def test_resolved_promise():
    p = Promise.resolved(42)
    assert p.is_completed()
    assert p.join() == 42

def test_rejected_promise():
    p = Promise.rejected(ValueError("Oops"))
    assert p.is_failed()
    with pytest.raises(ValueError):
        p.join()

def test_promise_of():
    p = Promise.of(lambda: 42)
    assert p.join() == 42
    assert p.is_completed()

def test_promise_of_failure():
    def failing():
        raise ValueError("Oops")
    p = Promise.of(failing)
    with pytest.raises(ValueError):
        p.join()
    assert p.is_failed()

def test_then():
    results = []
    p = Promise.resolved(42).then(lambda v: results.append(v))
    # Give it a moment to run the callback sync/async
    p.join()
    assert results == [42]

def test_catch():
    results = []
    p = Promise.rejected(ValueError("Oops")).catch(lambda e: results.append(str(e)))
    with pytest.raises(ValueError):
        p.join()
    assert results == ["Oops"]

def test_map():
    p = Promise.resolved(2).map(lambda x: x * 2)
    assert p.join() == 4

def test_flat_map():
    p = Promise.resolved(2).flat_map(lambda x: Promise.resolved(x * 2))
    assert p.join() == 4

def test_finally():
    results = []
    p = Promise.resolved(42).finally_(lambda: results.append("done"))
    p.join()
    assert results == ["done"]

def test_all():
    p = Promise.all(lambda: 1, lambda: 2, lambda: 3)
    assert p.join() == [1, 2, 3]

def test_all_failure():
    def fail(): raise ValueError("Fail")
    p = Promise.all(lambda: 1, fail, lambda: 3)
    with pytest.raises(PromiseAllError):
        p.join()

def test_race():
    def slow():
        time.sleep(0.1)
        return "slow"
    def fast():
        return "fast"
    p = Promise.race(slow, fast)
    assert p.join() == "fast"

def test_any():
    def fail(): raise ValueError("Fail")
    def slow_success():
        time.sleep(0.1)
        return "success"
    p = Promise.any(fail, slow_success)
    assert p.join() == "success"

def test_any_all_fail():
    def fail1(): raise ValueError("Fail 1")
    def fail2(): raise ValueError("Fail 2")
    p = Promise.any(fail1, fail2)
    with pytest.raises(PromiseAnyError):
        p.join()

def test_timeout():
    def slow():
        time.sleep(0.2)
        return 42
    p = Promise.of(slow).timeout(0.05)
    with pytest.raises(PromiseTimeoutError):
        p.join()

def test_cancel():
    def slow():
        time.sleep(0.2)
        return 42
    p = Promise.of(slow)
    p.cancel()
    assert p.is_cancelled()
    with pytest.raises(PromiseCancelledError):
        p.join()
