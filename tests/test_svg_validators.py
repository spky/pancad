import sys
from pathlib import Path
import unittest
import re

sys.path.append('src')

from PanCAD.svg import validators as sv

class TestSVGValidators(unittest.TestCase):
    
    def test_valid_stroke_linecap(self):
        answers = ["butt", "round", "square", "inherit"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    sv.stroke_linecap(ans),
                    ans)
    
    def test_valid_stroke_linecap_exceptions(self):
        answers = ["buttsss", 1, 0]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    sv.stroke_linecap(ans)
    
    def test_valid_stroke_linejoin(self):
        answers = ["miter", "round", "bevel", "inherit"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    sv.stroke_linejoin(ans),
                    ans)
    
    def test_valid_stroke_linejoin_exceptions(self):
        answers = ["buttsss", 1, 0]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    sv.stroke_linejoin(ans)
    
    def test_stroke_opacity(self):
        answers = [0, 0.0, 1, 1.0, 0.5]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    sv.stroke_opacity(ans),
                    str(ans))
                
    def test_stroke_opacity_exceptions(self):
        answers = ["test"]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    sv.stroke_opacity(ans)
    
    def test_color(self):
        answers = [
            "#ffffff",
            "#000000",
            "#fff",
            "#000",
            "rgb(255,255,255)",
            "rgb(0,0,0)",
            "rgb(10,10,10)",
            "Rgb(255,255,255)",
            "rGb(0,0,0)",
            "rgB(10,10,10)",
            "rgb(100%,100%,100%)",
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(sv.color(ans), str(ans))
    
    def test_color_exceptions(self):
        answers = [
            "#GGGGGG",
            "#GGG",
            "rgb(256,256,256)",
            "rgb(-1,-1,-1)",
            "rgb(101%,101%,101%)"
            "rgb(poot,poot,pott)"
            "rgb(100,100,100)rgb(100,100,100)"
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError, msg="Value given: "+str(ans)):
                    sv.color(ans)
    
    def test_paint(self):
        answers = [
            "#ffffff",
            "#000000",
            "#fff",
            "#000",
            "rgb(255,255,255)",
            "rgb(0,0,0)",
            "rgb(10,10,10)",
            "Rgb(255,255,255)",
            "rGb(0,0,0)",
            "rgB(10,10,10)",
            "rgb(100%,100%,100%)",
            "none",
            "currentColor",
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(sv.paint(ans), str(ans))
    
    def test_paint_exceptions(self):
        answers = [
            "#GGGGGG",
            "#GGG",
            "rgb(256,256,256)",
            "rgb(-1,-1,-1)",
            "rgb(101%,101%,101%)"
            "rgb(poot,poot,pott)"
            "rgb(100,100,100)rgb(100,100,100)"
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError, msg="Value given: "+str(ans)):
                    sv.paint(ans)
    
    def test_float_re(self):
        answers = ["1.0",1.0,"0.1",".1",".9",]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertTrue(re.match(f"^{sv.float_re}$", str(ans)))
    
    def test_int_str(self):
        answers = ["1",1,"9",9,1000,"1000"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertTrue(re.match(f"^{sv.integer_re}$", str(ans)))
    
    def test_number_re(self):
        answers = ["1",1,"9",9,1000,"1000","1.0",1.0,"0.1",".1",".9",]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertTrue(re.match(f"^{sv.number_re}$", str(ans)))
    
    def test_number(self):
        answers = ["1",1,"9",9,1000,"1000","1.0",1.0,"0.1",".1",".9",]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(sv.number(ans), str(ans))
    
    def test_percentage(self):
        answers = ["100%", "10.1%", "-10%"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(sv.percentage(ans), str(ans))
    
    def test_stroke_width(self):
        answers = [
            "1.01px",
            "1px",
            "1em",
            "1ex",
            "1in",
            "1cm",
            "1mm",
            "1pt",
            "1pc"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    sv.stroke_width(ans),
                    ans)
    
    def test_stroke_width_default_arg(self):
        answers = [1.01, 1]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    sv.stroke_width(ans),
                    str(ans))
    
    def test_stroke_width_exceptions(self):
        answers = [
            "-1.01in",
            "1.01slugs",
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError, msg="Value given: "+str(ans)):
                    sv.stroke_width(ans)
    
    def test_length_value(self):
        tests = [
            ["1in", 1],
            ["1.0in", 1.0],
            ["2223.0in", 2223.0],
            ["2223in", 2223],
            [1, 1],
            [1.0, 1.0],
            [-1.0, -1.0],
        ]
        for test in tests:
            with self.subTest(test=test):
                self.assertEqual(sv.length_value(test[0]), test[1])
    
    def test_length_unit(self):
        tests = [
            ["1in", "in"],
            ["1.0in", "in"],
            ["2223.0in", "in"],
            ["2223in", "in"],
            ["1.0em", "em"],
            ["1.0ex", "ex"],
            ["1.0px", "px"],
            ["1.0cm", "cm"],
            ["1.0mm", "mm"],
            ["1.0pt", "pt"],
            ["1.0pc", "pc"],
            ["1.0%", "%"],
            ["1.0%", "%"],
            ["1", ""],
            [1, ""],
            [1.0, ""],
            ["", ""],
            ["in", "in"],
        ]
        for t in tests:
            with self.subTest(t=t):
                self.assertEqual(sv.length_unit(t[0]), t[1])

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()