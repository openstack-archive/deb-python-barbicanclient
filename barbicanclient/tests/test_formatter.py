import testtools

from barbicanclient import formatter


class EntityFormatter(formatter.EntityFormatter):

    columns = ("Column A",
               "Column B",
               "Column C")

    def _get_formatted_data(self):
        data = (self._attr_a,
                self._attr_b,
                self._attr_c)
        return data


class Entity(EntityFormatter):

    def __init__(self, attr_a, attr_b, attr_c):
        self._attr_a = attr_a
        self._attr_b = attr_b
        self._attr_c = attr_c


class TestFormatter(testtools.TestCase):

    def test_should_get_list_objects(self):
        entity_1 = Entity('test_attr_a_1', 'test_attr_b_1', 'test_attr_c_1')
        entity_2 = Entity('test_attr_a_2', 'test_attr_b_2', 'test_attr_c_2')
        columns, data = EntityFormatter._list_objects([entity_1, entity_2])
        self.assertEqual(columns, ('Column A', 'Column B', 'Column C'))
        self.assertEqual([e for e in data],
                         [('test_attr_a_1', 'test_attr_b_1', 'test_attr_c_1'),
                          ('test_attr_a_2', 'test_attr_b_2', 'test_attr_c_2')])

    def test_should_get_list_objects_empty(self):
        columns, data = EntityFormatter._list_objects([])
        self.assertEqual(columns, [])
        self.assertEqual([e for e in data], [])

    def test_should_get_str(self):
        entity = Entity('test_attr_a_1', 'test_attr_b_1', 'test_attr_c_1')
        self.assertEqual(str(entity),
                         '+----------+---------------+\n'
                         '| Field    | Value         |\n'
                         '+----------+---------------+\n'
                         '| Column A | test_attr_a_1 |\n'
                         '| Column B | test_attr_b_1 |\n'
                         '| Column C | test_attr_c_1 |\n'
                         '+----------+---------------+')

    def test_should_to_dict(self):
        entity = Entity('test_attr_a_1', 'test_attr_b_1', 'test_attr_c_1')
        self.assertEqual(entity.to_dict(),
                         {'Column A': 'test_attr_a_1',
                          'Column B': 'test_attr_b_1',
                          'Column C': 'test_attr_c_1'})
