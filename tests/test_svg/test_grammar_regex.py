import unittest
import re

import PanCAD.graphics.svg.grammar_regex as gre

class TestWhiteSpace(unittest.TestCase):
    
    def test_wsp_whitespace_match(self):
        regex = re.compile(gre.WSP.dc)
        whitespace = [
            "\u0020", "\u0009", "\u000D", "\u000A",
            "foo\u000D", "\r", "\n", "\t", " "
        ]
        for character in whitespace:
            with self.subTest(pattern=regex.pattern, character=character):
                match = regex.search(character)
                self.assertTrue(match)
    
    def test_wsp_whitespace_not_match(self):
        regex = re.compile(gre.WSP.dc)
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
        regex = re.compile(gre.WSP.dc)
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
        regex = re.compile(gre.comma_wsp.dc)
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
        regex = re.compile(gre.comma_wsp.dc)
        tests = [
            "AA", "A|A",
        ]
        for string in tests:
            with self.subTest(pattern=regex.pattern, string=string):
                match = regex.search(string)
                self.assertFalse(match)

class TestNumbers(unittest.TestCase):
    
    def test_exponent_match(self):
        regex = re.compile(gre.exponent.dc)
        tests = [
            "E100","e100", "e+100", "e-100",
        ]
        for string in tests:
            with self.subTest(pattern=regex.pattern, string=string):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_fractional_constant(self):
        regex = re.compile(gre.fractional_const.dc)
        tests = [
            "1.1", ".1", "1."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_floating_point_constant_match(self):
        regex = re.compile(gre.float_const.dc)
        tests = [
            "10E100", "1.100E+100", ".100E-100", "100.", "0.100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_floating_point_constant_not_match(self):
        regex = re.compile(gre.float_const.dc)
        tests = [
            "E", "E+100", ".E-100", "."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertFalse(match)
    
    def test_number_match(self):
        regex = re.compile(gre.number.dc)
        tests = [
            "1", "10", "1e-100", "1.100", "1.100e+100", ".100", "-.100",
            "+1", "+1.1", "-1."
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertEqual(regex.search(string)[0], string)
    
    def test_nonnegative_number_match(self):
        regex = re.compile(gre.nonnegative_number.dc)
        tests = [
            "1", "1.0", "1e-100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertEqual(regex.search(string)[0], string)
    
    def test_nonnegative_number_not_match(self):
        regex = re.compile(gre.nonnegative_number.dc)
        tests = [
            "-1", "-1.0", "-1e-100"
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                self.assertNotEqual(regex.search(string)[0], string)
    
    # def test_fractional_constant_decimal_exponent(self):
        # regex = re.compile(gre._frac_const_dec_exp)
        # tests = [
            # ("1.1e-100", None, "1", "1", "-", "100"),
            # ("1.1", None, "1", "1", None, None),
            # ("-1.1", "-", "1", "1", None, None),
        # ]
        # for string, sign, whole, decimal, exp_sign, exponent in tests:
            # with self.subTest(string=string, pattern=regex.pattern):
                # match = regex.search(string)
                # results = (
                    # match.group("sign"),
                    # match.group("whole_number"),
                    # match.group("decimal_number"),
                    # match.group("exponent_sign"),
                    # match.group("exponent_number"),
                # )
                # self.assertEqual(results,
                                 # (sign, whole, decimal, exp_sign, exponent))
    
    # def test_fractional_constant_exponent(self):
        # regex = re.compile(gre._frac_const_exp)
        # tests = [
            # ("1.e-100", None, "1", "-", "100"),
            # ("1.", None, "1", None, None),
            # ("-1.", "-", "1", None, None),
        # ]
        # for string, sign, whole, exp_sign, exponent in tests:
            # with self.subTest(string=string, pattern=regex.pattern):
                # match = regex.search(string)
                # results = (
                    # match.group("sign"),
                    # match.group("whole_number"),
                    # match.group("exponent_sign"),
                    # match.group("exponent_number"),
                # )
                # self.assertEqual(results,
                                 # (sign, whole, exp_sign, exponent))
    
    # def test_int_constant_exponent(self):
        # regex = re.compile(gre._int_const_exp)
        # tests = [
            # ("1e-100", None, "1", "-", "100"),
            # ("10e+100", None, "10", "+", "100"),
            # ("10e100", None, "10", None, "100"),
            # ("10", None, "10", None, None),
            # ("-10", "-", "10", None, None),
        # ]
        # for string, sign, whole, exp_sign, exponent in tests:
            # with self.subTest(string=string, pattern=regex.pattern):
                # match = regex.search(string)
                # results = (
                    # match.group("sign"),
                    # match.group("whole_number"),
                    # match.group("exponent_sign"),
                    # match.group("exponent_number"),
                # )
                # self.assertEqual(results,
                                 # (sign, whole, exp_sign, exponent))
    
    # def test_parse_number(self):
        # tests = [
            # ("1e-100", 1e-100),
        # ]
        # # result = gre.parse_number(

class TestCoordinates(unittest.TestCase):
    
    def test_coordinate_pair_match(self):
        regex = re.compile(gre.coordinate_pair.dc)
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
        regex = re.compile(gre.coordinate_pair.dc)
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
        regex = re.compile(gre.coordinate_pair_sequence.dc)
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
        regex = re.compile(gre.coordinate_pair_sequence.dc)
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
        regex = re.compile(gre.coordinate_sequence.dc)
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
        regex = re.compile(gre.moveto)
        tests = [
            "M1,1",
            "M 1 1 2 2",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_horizontal_lineto(self):
        regex = re.compile(gre.horizontal_lineto)
        tests = [
            "H1",
            "H 1 2",
        ]
        for string in tests:
            with self.subTest(string=string, pattern=regex.pattern):
                match = regex.search(string)
                self.assertEqual(match[0], string)
    
    def test_elliptical_arc(self):
        regex = re.compile(gre.elliptical_arc)
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
        regex = re.compile(gre.command)
        tests = [
            ("M 1 1 L 2 2", ("M 1 1 ", "L 2 2")),
            ("M1,1L2,2", ("M1,1", "L2,2")),
            ("M 1 1 L 2 2z", ("M 1 1 ", "L 2 2", "z")),
            ("M 1 1 L 2 2A3 3 2 1 1 0 0", ("M 1 1 ", "L 2 2", "A3 3 2 1 1 0 0")),
            ("   M 1 1 L 2 2A3 3 2 1 1 0 0", ("M 1 1 ", "L 2 2", "A3 3 2 1 1 0 0")),
        ]
        for string, expected in tests:
            with self.subTest(string=string):
                matches = regex.findall(string)
                self.assertEqual(tuple(matches), expected)

if __name__ == "__main__":
    unittest.main()