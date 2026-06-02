"""
tests/test_collections.py
-------------------------
Basic test suite for Nestifypy Collections module.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nestifypy.collections import (
    ArrayList, LinkedList, Stack, Queue, OrderedSet, HashMap
)

def test_array_list():
    al = ArrayList([1, 2, 3])
    al.add(4).remove(2)
    
    assert al.size() == 3
    assert al.contains(1)
    assert not al.contains(2)
    assert al.first() == 1
    assert al.last() == 4
    
    mapped = al.map(lambda x: x * 2)
    assert mapped.to_list() == [2, 6, 8]
    
    filtered = al.filter(lambda x: x > 1)
    assert filtered.to_list() == [3, 4]

def test_linked_list():
    ll = LinkedList([2, 3])
    ll.add_first(1).add_last(4)
    
    assert ll.size() == 4
    assert ll.peek_first() == 1
    assert ll.peek_last() == 4
    
    assert ll.remove_first() == 1
    assert ll.remove_last() == 4
    assert ll.to_list() == [2, 3]

def test_stack():
    s = Stack()
    s.push(1).push(2).push(3)
    
    assert s.size() == 3
    assert s.peek() == 3
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1
    assert s.is_empty()

def test_queue():
    q = Queue()
    q.enqueue(1).enqueue(2).enqueue(3)
    
    assert q.size() == 3
    assert q.peek() == 1
    assert q.dequeue() == 1
    assert q.dequeue() == 2
    assert q.dequeue() == 3
    assert q.is_empty()

def test_ordered_set():
    os = OrderedSet([1, 2, 2, 3])
    assert os.to_list() == [1, 2, 3]
    
    os.add(4).remove(2)
    assert os.to_list() == [1, 3, 4]
    
    other = [3, 4, 5]
    assert os.union(other).to_list() == [1, 3, 4, 5]
    assert os.intersection(other).to_list() == [3, 4]

def test_hash_map():
    hm = HashMap({"a": 1, "b": 2})
    hm.put("c", 3)
    
    assert hm.get("a") == 1
    assert hm.get_or("z", 99) == 99
    assert hm.contains_key("b")
    assert hm.contains_value(3)
    
    hm.remove("b")
    assert not hm.contains_key("b")
    
    mapped = hm.map_values(lambda v: v * 10)
    assert mapped.get("a") == 10
    assert mapped.get("c") == 30
