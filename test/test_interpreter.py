import unittest

import cpu4.interpreter as i


class TestInterpreter(unittest.TestCase):
    def test_empty(self):
        i.parse('')
        self.assertEqual(i.print_formatted(), '')

    def test_label(self):
        i.parse('label:')
        self.assertEqual(i.print_formatted(), '0 label:')

        i.parse(' LABEL : ')
        self.assertEqual(i.print_formatted(), '0 label:')

        i.parse(' label: \n lbl : ')
        self.assertEqual(i.print_formatted(), '0 label:\n'
                                    '1 lbl:')

    def test_statement(self):
        i.parse('statement')
        self.assertEqual(i.print_formatted(), '0 statement')

        i.parse(' STATEMENT ')
        self.assertEqual(i.print_formatted(), '0 statement')

        i.parse(' statement \n stmt ')
        self.assertEqual(i.print_formatted(), '0 statement\n'
                                    '1 stmt')

    def test_comment(self):
        i.parse('; comment')
        self.assertEqual(i.print_formatted(), '0 ; comment')

        i.parse(' ;COMMENT ')
        self.assertEqual(i.print_formatted(), '0 ;COMMENT')

        i.parse(' ;comment \n; c ')
        self.assertEqual(i.print_formatted(), '0 ;comment\n'
                                    '1 ; c')

    def test_line(self):
        i.parse('\n'*20)
        self.assertEqual(i.print_formatted(), '\n'.join((f'{i:02X}' for i in range(20))))

    def test_combined(self):
        i.parse('''
 l: s ;c
LBL: STMT ; COM
''')
        self.assertEqual(i.print_raw(), '''0 
1  l: s ;c
2 LBL: STMT ; COM''')
        self.assertEqual(i.print_formatted(), '''0
1 l:   s    ;c
2 lbl: stmt ; COM''')
