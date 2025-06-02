import unittest
import re

import PanCAD.graphics.svg.grammar_regex as gre

class TestWhiteSpace(unittest.TestCase):
    
    def test_wsp_whitespace_match(self):
        regex = re.compile(gre.WSP)
        whitespace = [
            "\u0020", "\u0009", "\u000D", "\u000A",
            "foo\u000D", "\r", "\n", "\t", " "
        ]
        for character in whitespace:
            with self.subTest(pattern=regex.pattern, character=character):
                match = regex.search(character)
                self.assertTrue(match)
    
    def test_wsp_whitespace_not_match(self):
        regex = re.compile(gre.WSP)
        # Whitespace Characters not specified in svg standard
        whitespace = [
            # Characters
            "a", "1",
            # Vertical Tab, Form Feed, Next Line, Line Separator,
            # and Paragraph Separator
            "\u000B", "\u000C", "\u0085", "\u2028", "\u2029"
             # Non-breaking space
            "\u00A0",
             # Different Length Spaces
            "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007",
        ]
        for character in whitespace:
            with self.subTest(pattern=regex.pattern, character=character):
                match = regex.search(character)
                self.assertFalse(match)
    
    def test_wsp_multi_whitespace(self):
        regex = re.compile(gre.WSP)
        whitespace = [
            "\u0020\u0020",
            "\u0009\u0009",
            "\u000D\u000D",
            "\u000A\u000A",
            "\r\r",
            "\n\n",
            "\t\t",
            "  ",
        ]
        for character in whitespace:
            with self.subTest(pattern=regex.pattern, character=character):
                matches = regex.findall(character)
                self.assertEqual(len(matches), 2)
    
    def test_comma_wsp_match(self):
        regex = re.compile(gre.COMMA_WSP)
        # print(regex.pattern.encode("utf-8"))
        tests = [
            ("A, A", ", "),
            ("A,A", ","),
            ("A A", " "),
            ("A ,A", " ,"),
            ("A , A", " , "),
            ("A  A", "  "),
            ("A  ,  A", "  ,  "),
        ]
        for string, expected in tests:
            with self.subTest(string=string, expected=expected,
                              pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], expected)
    
    def test_comma_wsp_not_match(self):
        regex = re.compile(gre.COMMA_WSP)
        tests = [
            "AA", "A|A",
        ]
        for string in tests:
            with self.subTest(pattern=regex.pattern, string=string):
                match = regex.search(string)
                self.assertFalse(match)

class TestNumbers(unittest.TestCase):
    
    def test_exponent_match(self):
        regex = re.compile(gre.EXPONENT)
        tests = [
            "E100","e100", "e+100", "e-100",
        ]
        for string in tests:
            with self.subTest(pattern=regex.pattern, string=string):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_fractional_constant(self):
        regex = re.compile(gre.FRACTIONAL_CONST)
        tests = [
            "1.1", ".1", "1."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_floating_point_constant_match(self):
        regex = re.compile(gre.FLOAT_CONST)
        tests = [
            "10E100", "1.100E+100", ".100E-100", "100.", "0.100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_floating_point_constant_not_match(self):
        regex = re.compile(gre.FLOAT_CONST)
        tests = [
            "E", "E+100", ".E-100", "."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertFalse(match)
    
    def test_number_match(self):
        regex = re.compile(gre.NUMBER)
        tests = [
            "1", "10", "1e-100", "1.100", "1.100e+100", ".100", "-.100",
            "+1", "+1.1", "-1."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertEqual(regex.search(string)[0], string)
    
    def test_nonnegative_number_match(self):
        regex = re.compile(gre.NONNEGATIVE_NUMBER)
        tests = [
            "1", "1.0", "1e-100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertEqual(regex.search(string)[0], string)
    
    def test_nonnegative_number_not_match(self):
        regex = re.compile(gre.NONNEGATIVE_NUMBER)
        tests = [
            "-1", "-1.0", "-1e-100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertNotEqual(regex.search(string)[0], string)

class TestCoordinates(unittest.TestCase):
    
    def test_coordinate_pair_match(self):
        regex = re.compile(gre.COORDINATE_PAIR)
        tests = [
            "1,1",
            "1, 1",
            "1, \n1",
            "1 , 1",
            "1.0 , 1.0",
            "1.0e+10 , 1.0",
            "1.0 , 1.0e+10",
            "1 , 1.0e+10",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_coordinate_pair_not_match(self):
        regex = re.compile(gre.COORDINATE_PAIR)
        tests = [
            "1",
            "11",
            "1,,1",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertFalse(match)
    
    def test_coordinate_pair_sequence_match(self):
        regex = re.compile(gre.COORDINATE_PAIR_SEQUENCE)
        tests = [
            "1,1",
            "1,1 1,1",
            "1,1,1,1",
            "1 1 1 1",
            "1 1\n1 1",
            "1,1 1,1 1,1",
            "1,1,1,1,1,1",
            "1 1\n1 1\n1 1",
            "1.0,1.0,1,1.0,1,1.0",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_coordinate_pair_sequence_not_match(self):
        regex = re.compile(gre.COORDINATE_PAIR_SEQUENCE)
        tests = [
            "a",
            "1,1,1",
            "1 1 1",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertNotEqual(match, string)
    
    def test_coordinate_sequence_match(self):
        regex = re.compile(gre.COORDINATE_SEQUENCE)
        tests = [
            "1,1",
            "1,1, 1",
            "1,1 1,1",
            "1,1,1,1",
            "1 1 1 1",
            "1 1\n1 1",
            "1,1 1,1 1,1",
            "1,1,1,1,1,1",
            "1 1\n1 1\n1 1",
            "1.0,1.0,1,1.0,1,1.0",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)

class TestCommands(unittest.TestCase):
    
    def test_moveto(self):
        regex = re.compile(gre.MOVETO)
        tests = [
            "M1,1",
            "M 1 1 2 2",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_horizontal_lineto(self):
        regex = re.compile(gre.HORIZONTAL_LINETO)
        tests = [
            "H1",
            "H 1 2",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_elliptical_arc_arg(self):
        regex = re.compile(gre.ELLIPTICAL_ARC_ARG)
        tests = [
            "3 3 2 1 1 0 0",
            "3.3 3.3 -1.1 1 1 0 0",
            "3.3 3.3 -1.1 0 0 0 0",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_elliptical_arc(self):
        regex = re.compile(gre.ELLIPTICAL_ARC)
        tests = [
            "A3 3 2 1 1 0 0",
            "A3.3 3.3 -1.1 1 1 0 0",
            "A3.3 3.3 -1.1 0 0 0 0",
            "A 3.3 3.3 -1.1 0 0 0 0",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_command(self):
        regex = re.compile(gre.COMMAND)
        tests = [
            ("M 1 1 L 2 2", ("M 1 1 ", "L 2 2")),
            ("M1,1L2,2", ("M1,1", "L2,2")),
            ("M 1 1 L 2 2z", ("M 1 1 ", "L 2 2", "z")),
        ]
        for string, expected in tests:
            with self.subTest(string=string):
                matches = regex.findall(string)
                match_tuple = tuple()
                for m in matches:
                    match_tuple += (m[0],)
                self.assertEqual(match_tuple, expected)

if __name__ == "__main__":
    unittest.main()