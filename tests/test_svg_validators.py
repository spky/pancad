import sys
from pathlib import Path
import unittest

sys.path.append('src')

from svg_validators import (
    stroke_linecap,
    stroke_linejoin,
    stroke_opacity,
    color,
    fill,
    stroke,
    stroke_width,
)

class TestSVGValidators(unittest.TestCase):
    
    def test_valid_stroke_linecap(self):
        answers = ["butt", "round", "square", "inherit"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    stroke_linecap(ans),
                    "stroke-linecap:" + ans)
    
    def test_valid_stroke_linecap_exceptions(self):
        answers = ["buttsss", 1, 0]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    stroke_linecap(ans)
    
    def test_valid_stroke_linejoin(self):
        answers = ["miter", "round", "bevel", "inherit"]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    stroke_linejoin(ans),
                    "stroke-linejoin:" + ans)
    
    def test_valid_stroke_linejoin_exceptions(self):
        answers = ["buttsss", 1, 0]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    stroke_linejoin(ans)
    
    def test_stroke_opacity(self):
        answers = [0, 0.0, 1, 1.0, 0.5]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    stroke_opacity(ans),
                    "stroke-opacity:" + str(ans))
                
    def test_stroke_opacity_exceptions(self):
        answers = [-1, -0.1, 1.1, 2, 10, "test"]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError):
                    stroke_opacity(ans)
    
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
                self.assertEqual(color(ans), str(ans))
    
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
                    color(ans)
    
    def test_fill(self):
        answers = [
            "#FFFFFF",
            "none"
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(fill(ans), "fill:"+ans)
    
    def test_stroke(self):
        self.assertEqual(stroke("#FFFFFF"), "stroke:#FFFFFF")
    
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
                    stroke_width(ans),
                    "stroke-width:" + ans)
    
    def test_stroke_width_default_arg(self):
        answers = [1.01, 1]
        for ans in answers:
            with self.subTest(ans=ans):
                self.assertEqual(
                    stroke_width(ans),
                    "stroke-width:" + str(ans))
    
    def test_stroke_width_exceptions(self):
        answers = [
            "-1.01in",
            "1.01slugs",
        ]
        for ans in answers:
            with self.subTest(ans=ans):
                with self.assertRaises(ValueError, msg="Value given: "+str(ans)):
                    stroke_width(ans)

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()