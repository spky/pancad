import sys
import unittest

sys.path.append('src')

from svg_validators import (
    stroke_linecap,
    stroke_linejoin,
    stroke_opacity,
    color,
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
        answers = ["mitre", "round", "bevel", "inherit"]
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

if __name__ == "__main__":
    unittest.main()