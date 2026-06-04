import pytest
from arkhe.trying import Try, Success, Failure, TryError, FilterError, EmptyValueError

def test_try_success():
    result = Try.of(lambda: 42)
    assert result.is_success()
    assert not result.is_failure()
    assert result.get() == 42
    assert result.get_or_default(0) == 42
    assert result.get_or_none() == 42
    assert result.get_error() is None

def test_try_failure():
    def failing():
        raise ValueError("Oops")
    
    result = Try.of(failing)
    assert result.is_failure()
    assert not result.is_success()
    
    with pytest.raises(ValueError):
        result.get()
        
    assert result.get_or_default(0) == 0
    assert result.get_or_none() is None
    assert isinstance(result.get_error(), ValueError)

def test_map():
    success = Try.of(lambda: 2).map(lambda x: x * 2)
    assert success.get() == 4

    def failing():
        raise ValueError("Oops")
    
    failure = Try.of(failing).map(lambda x: x * 2)
    assert failure.is_failure()
    assert isinstance(failure.get_error(), ValueError)

def test_flat_map():
    def double_try(x):
        return Try.of(lambda: x * 2)
        
    success = Try.of(lambda: 2).flat_map(double_try)
    assert success.get() == 4

    def fail_try(x):
        return Try.failure(ValueError("Flatmap fail"))
        
    failure = Try.of(lambda: 2).flat_map(fail_try)
    assert failure.is_failure()
    assert isinstance(failure.get_error(), ValueError)

def test_filter():
    success = Try.of(lambda: 2).filter(lambda x: x == 2)
    assert success.get() == 2

    failure = Try.of(lambda: 2).filter(lambda x: x == 3, "Not 3")
    assert failure.is_failure()
    assert isinstance(failure.get_error(), FilterError)

def test_recover():
    result = Try.failure(ValueError("Oops")).recover(lambda e: 42)
    assert result.is_success()
    assert result.get() == 42

def test_recover_with():
    result = Try.failure(ValueError("Oops")).recover_with(lambda e: Try.success(42))
    assert result.is_success()
    assert result.get() == 42

def test_of_nullable():
    assert Try.of_nullable(42).get() == 42
    assert Try.of_nullable(None).is_failure()
