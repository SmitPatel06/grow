from . import document_cache
from . import pods
from . import storage
from grow.testing import testing
import unittest


class DocumentCacheTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.doc_cache = document_cache.DocumentCache()

    def test_add(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])

    def test_add_all(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        print str(doc._locale_kwarg)
        self.doc_cache.add_all({
            '/content/pages/intro.md': {
                'question': '???'
            }
        })
        self.assertEqual('???', self.doc_cache.get(doc)['question'])

    def test_add_property(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.doc_cache.add_property(doc, 'answer', 42)
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])

    def test_delete(self):
        value = {
            'answer': 42
        }
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.doc_cache.add(doc, value)
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])
        self.assertEqual(value, self.doc_cache.delete(doc))
        self.assertEqual(None, self.doc_cache.get(doc))

    def test_export(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        doc = self.pod.get_doc('/content/pages/about.md')
        self.doc_cache.add(doc, {
            'question': '???'
        })
        self.assertDictEqual({
            '/content/pages/about.md': {
                'question': '???'
            },
            '/content/pages/intro.md': {
                'answer': 42
            },
        }, self.doc_cache.export())

    def test_get_property(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        self.assertEqual(42, self.doc_cache.get_property(doc, 'answer'))


if __name__ == '__main__':
    unittest.main()
