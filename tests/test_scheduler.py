import pytest
import time
from nestifypy.scheduler import Scheduler, JobState

def test_scheduler_after():
    results = []
    def task():
        results.append(1)
    
    job = Scheduler.after(0.1).seconds(task)
    time.sleep(0.2)
    assert results == [1]
    assert job.completed()

def test_scheduler_every():
    results = []
    def task():
        results.append(1)
        
    job = Scheduler.every(0.1).seconds(task)
    time.sleep(0.25)
    job.cancel()
    assert len(results) >= 2
    assert job.cancelled()

def test_scheduler_cancel():
    results = []
    def task():
        results.append(1)
        
    job = Scheduler.after(0.5).seconds(task)
    job.cancel()
    time.sleep(0.6)
    assert results == []
    assert job.cancelled()

def test_scheduler_pause_resume():
    results = []
    def task():
        results.append(1)
        
    job = Scheduler.every(0.1).seconds(task)
    # The first execution happens immediately, so we should have 1 result.
    job.pause()
    time.sleep(0.25)
    assert len(results) >= 1
    assert job.paused()
    
    count_before = len(results)
    job.resume()
    time.sleep(0.2)
    job.cancel()
    assert len(results) > count_before
    
def test_scheduler_named():
    def task(): pass
    job = Scheduler.after(10).seconds(task).named("my_job")
    assert job.name == "my_job"
    job.cancel()
