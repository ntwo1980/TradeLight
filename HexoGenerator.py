import os
import datetime
import unittest
import pandas as pd

class HexoGenerator:
    def __init__(self, hexo_file_path, title, **kwargs):
        self.lines = []

        self.hexo_file_path = hexo_file_path
        self.title = title
        self.time = datetime.datetime.now() if 'time' not in kwargs else kwargs['time']
        self.tags = [] if 'tags' not in kwargs else kwargs['tags']
        if not isinstance(self.tags, list):
            self.tags = [self.tags]

        self.lines.append('-' * 3)
        self.lines.append('title: {}'.format(self.title))
        self.lines.append('date: {}'.format(self.time.strftime('%Y-%m-%d %H:%M:%S')))
        if self.tags:
            self.lines.append('tags:')
            self.lines.append(os.linesep.join(['- {}'.format(l) for l in self.tags]))
        self.lines.append('-' * 3)
        self.empty_line()

    def empty_line(self):
        self.lines.append('')

    def h1(self, text):
        self.header(1, text)

    def h2(self, text):
        self.header(2, text)

    def h3(self, text):
        self.header(3, text)

    def h4(self, text):
        self.header(4, text)

    def h5(self, text):
        self.header(5, text)

    def header(self, level, text):
        self.lines.append('{} {}'.format('#' * level, text))
        self.empty_line()

    def line(self, text):
        self.lines.append(text)
        self.empty_line()

    def img(self, url):
        self.lines.append('![]({})'.format(url))
        self.empty_line()

    def data_frame(self, df, headers = None, float_format='%.2g'):
        text = os.linesep.join([
                '|'.join(df.columns),
                '|'.join(4 * '-' for i in df.columns),
                df.to_csv(sep='|', index=False, header=False, float_format=float_format)
            ]).replace('|', ' | ')
        self.line(text)


    def __str__(self):
        return os.linesep.join(self.lines)

    def write(self):
        with open(self.hexo_file_path, 'w') as f:
            f.write(str(self))

class HexoGeneratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        pass

    @classmethod
    def tearDownClass(self):
        pass

    def test_empty_hexo_file(self):
        generator = HexoGenerator('test.md', 'test', tags=['tag1', 'tag2'])
        generator.h1('header1')
        generator.h2('header2')
        generator.h3('header3')
        generator.h4('header4')
        generator.h5('header5')

        generator.line('line test ' * 10)

        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6], 'col3': [7, 8, 9]})
        generator.data_frame(df)

        print(generator)

if __name__ == '__main__':
    unittest.main()

