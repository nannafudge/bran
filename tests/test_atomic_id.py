import concurrent.futures

import pytest

from pybran.decorators import Id, TypeId, NameId


@pytest.fixture(autouse=True)
def reset_id():
    Id.instance().reset()
    TypeId.instance().reset()
    NameId.instance().reset()


def test_atomic_id():
    assert Id.instance().get_id() == 1
    assert Id.instance().get_id() == 2


def test_type_id_and_name_id():
    assert TypeId.instance().get_id() == 1
    assert TypeId.instance().get_id() == 2
    assert NameId.instance().get_id() == 1
    assert NameId.instance().get_id() == 2


def test_id_from_another_thread():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = [result for result in executor.map(_id, range(3))]
        assert results == [1, 2, 3]


def _id(i):
    return Id.instance().get_id()
