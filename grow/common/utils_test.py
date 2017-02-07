from grow.testing import testing
from grow.common.sdk_utils import get_this_version, LatestVersionCheckError
from grow.pods import errors
from . import utils
import copy
import mock
import semantic_version
import unittest


class UtilsTestCase(unittest.TestCase):

    def test_clean_google_href(self):
        # Test without a match.
        raw_input = '<a href="https://grow.io/">Link</a>'
        expected = '<a href="https://grow.io/">Link</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with ?q=
        raw_input = '<a href="https://www.google.com/url?q=https%3A%2F%2Fgrow.io%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.io/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with &q=
        raw_input = '<a href="https://www.google.com/url?sa=t&q=https%3A%2F%2Fgrow.io%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.io/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

    def test_clean_html_markdown(self):
        # Test without a match.
        raw_input = '<a href="https://grow.io/">Link</a>'
        expected = '[Link](https://grow.io/)'
        actual = utils.clean_html(raw_input, convert_to_markdown=True)
        self.assertEqual(expected, actual)

    def test_every_two(self):
        raw_input = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [(1, 2), (3, 4), (5, 6), (7, 8)]
        actual = utils.every_two(raw_input)
        self.assertEqual(expected, actual)

    def test_parse_yaml(self):
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')
        result = utils.parse_yaml(content, pod=pod)
        doc = pod.get_doc('/content/pages/home.yaml')
        self.assertEqual(doc, result['doc'])
        expected_docs = [
            pod.get_doc('/content/pages/home.yaml'),
            pod.get_doc('/content/pages/about.yaml'),
            pod.get_doc('/content/pages/home.yaml'),
        ]
        self.assertEqual(expected_docs, result['docs'])

    def test_process_google_comments(self):
        # Google comment link.
        raw = '<div><a id="cmnt" href="https://grow.io/">Link</a></div>'
        expected = ''
        actual = utils.clean_html(raw)
        self.assertEqual(expected, actual)

        # Google footnote link.
        raw = '<sup><a id="ftnt" href="https://grow.io/">Link</a></sup>'
        expected = ''
        actual = utils.clean_html(raw)
        self.assertEqual(expected, actual)

    def test_untag_fields(self):
        fields_to_test = {
            'title': 'value-none',
            'title@fr': 'value-fr',
            'list': [
                {
                    'list-item-title': 'value-none',
                    'list-item-title@fr': 'value-fr',
                },
            ],
            'sub-nested': {
                'sub-nested': {
                    'nested@': 'sub-sub-nested-value',
                },
            },
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title@': 'nested-value-none',
            },
            'nested@fr': {
                'nested-title@': 'nested-value-fr',
            },
            'list@de': [
                'list-item-de',
            ]
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-fr',
            'list': [{'list-item-title': 'value-fr'},],
            'nested': {'nested-title': 'nested-value-fr',},
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, utils.untag_fields(fields, locale='fr'))

        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-none',
            'list': ['list-item-de',],
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title': 'nested-value-none',
            },
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, utils.untag_fields(fields, locale='de'))

        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
                'nested@fr': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-fr',
            },
        }, utils.untag_fields(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='de'))

        fields_to_test = {
            'list': [
                {
                    'item': 'value-1',
                    'item@de': 'value-1-de',
                    'item@fr': 'value-1-fr',
                },
                {
                    'item': 'value-2',
                },
                {
                    'item@fr': 'value-3-fr',
                },
            ]
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1-fr',
                },
                {
                    'item': 'value-2',
                },
                {
                    'item': 'value-3-fr',
                },
            ]
        }, utils.untag_fields(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1-de',
                },
                {
                    'item': 'value-2',
                },
                {},
            ]
        }, utils.untag_fields(fields, locale='de'))
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1',
                },
                {
                    'item': 'value-2',
                },
                {},
            ]
        }, utils.untag_fields(fields, locale='ja'))

        fields_to_test = {
            '$view': '/views/base.html',
            '$view@ja': '/views/base-ja.html',
            'qaz': 'qux',
            'qaz@ja': 'qux-ja',
            'qaz@de': 'qux-de',
            'qaz@ja': 'qux-ja',
            'foo': 'bar-base',
            'foo@en': 'bar-en',
            'foo@de': 'bar-de',
            'foo@ja': 'bar-ja',
            'nested': {
                'nested': 'nested-base',
                'nested@ja': 'nested-ja',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base-ja.html',
            'qaz': 'qux-ja',
            'foo': 'bar-ja',
            'nested': {
                'nested': 'nested-ja',
            },
        }, utils.untag_fields(fields, locale='ja'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base.html',
            'qaz': 'qux-de',
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='de'))

        fields_to_test = {
            'foo@': 'bar',
            'foo@fr@': 'bar-fr',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar',
        }, utils.untag_fields(fields))
        self.assertDictEqual({
            'foo': 'bar',
        }, utils.untag_fields(fields, locale='de'))
        self.assertDictEqual({
            'foo': 'bar-fr',
        }, utils.untag_fields(fields, locale='fr'))

        fields_to_test = {
            'list@': [
                'value1',
                'value2',
                'value3',
            ],
            'list@fr': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                'value1',
                'value2',
                'value3',
            ],
            'list@': [
                'value1',
                'value2',
                'value3',
            ],
        }, utils.untag_fields(fields, locale='de'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
            'list@': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
        }, utils.untag_fields(fields, locale='fr'))

        fields_to_test = {
            'nested1': {
                'list@': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
                'list@fr@': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
            },
            'nested2': {
                'list@': [
                    'value1',
                    'value2',
                ],
                'list@fr@': [
                    'value1-fr',
                    'value2-fr',
                ],
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested1': {
                'list': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
                'list@': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
            },
            'nested2': {
                'list': [
                    'value1',
                    'value2',
                ],
                'list@': [
                    'value1',
                    'value2',
                ],
            },
        }, utils.untag_fields(fields, locale='de'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested1': {
                'list': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
                'list@': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
            },
            'nested2': {
                'list': [
                    'value1-fr',
                    'value2-fr',
                ],
                'list@': [
                    'value1-fr',
                    'value2-fr',
                ],
            },
        }, utils.untag_fields(fields, locale='fr'))

    def test_untag_fields_with_backwards_compatibility(self):
        fields_to_test = {
            'title@': 'foo',
            'nested': {
                'list@': [
                    'value1',
                ],
            },
            'list@': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'foo',
            'list': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
            'list@': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
            'nested': {
                'list': [
                    'value1',
                ],
                'list@': [
                    'value1',
                ],
            },
        }, utils.untag_fields(fields))

    def test_untag_fields_with_regex(self):
        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr.*': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
                'nested@de_AT': 'nested-de',
                'nested@fr': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-fr',
            },
        }, utils.untag_fields(fields, locale='fr'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='fr_FR'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='fr_CA'))
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='de'))
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-de',
            },
        }, utils.untag_fields(fields, locale='de_AT'))

        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr|it': 'bar-any',
            'nested': {
                'nested': 'nested-base',
                'nested@fr|it': 'nested-any',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-any',
            'nested': {
                'nested': 'nested-any',
            },
        }, utils.untag_fields(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-any',
            'nested': {
                'nested': 'nested-any',
            },
        }, utils.untag_fields(fields, locale='it'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, utils.untag_fields(fields, locale='de'))

    def test_validate_name(self):
        with self.assertRaises(errors.BadNameError):
            utils.validate_name('//you/shall/not/pass')

        with self.assertRaises(errors.BadNameError):
            utils.validate_name('../you/shall/not/pass')

        with self.assertRaises(errors.BadNameError):
            utils.validate_name('/you/shall not/pass')

        utils.validate_name('c:\you\shall\pass')
        utils.validate_name('/you/shall/pass')
        utils.validate_name('you/shall/pass')
        utils.validate_name('./you/shall/pass')
        utils.validate_name(u'\xbe4/\xb05/\xb93')

    def test_version_enforcement(self):
        with mock.patch('grow.pods.pods.Pod.grow_version',
                        new_callable=mock.PropertyMock) as mock_version:
            this_version = get_this_version()
            gt_version = '>{0}'.format(semantic_version.Version(this_version))
            mock_version.return_value = gt_version
            with self.assertRaises(LatestVersionCheckError):
                pod = testing.create_test_pod()

    def test_walk(self):
        data = {
          'foo': 'bar',
          'bam': {
            'foo': 'bar2',
            'foo2': ['bar3', 'bar4'],
          }
        }

        actual = []
        callback = lambda item, key, node: actual.append(item)
        utils.walk(data, callback)

        expected = ['bar', 'bar2', 'bar3', 'bar4']
        self.assertItemsEqual(expected, actual)

    def test_walk_empty(self):
        data = None

        actual = []
        callback = lambda item, key, node: actual.append(item)
        utils.walk(data, callback)

        expected = []
        self.assertItemsEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
