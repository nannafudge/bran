import concurrent.futures

from pybran import Id, TypeId, NameId


class TestAtomicId:
    def test_atomic_id(self):
        assert Id().get_id() == 1
        assert Id().get_id() == 2

    def test_type_id_and_name_id_not_linked(self):
        type_id = TypeId().get_id()
        NameId().get_id()

        assert TypeId().get_id() == type_id + 1

    def test_id_from_another_thread(self):
        results = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(lambda i: Id().get_id(), range(3))

            # Assert we receive 3 unique results
            assert len({result for result in results}) == 3
