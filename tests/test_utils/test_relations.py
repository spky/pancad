from unittest import TestCase
from functools import partial
from textwrap import indent
from pprint import pp
from typing import Hashable

from pancad.utils.relations import OneToOne, OneToMany

class OneToOneBasicFunc(TestCase):
    
    def setUp(self):
        self.source_id = "source"
        self.target_id = "target"
        self.marker = "relation_type"
    
    def test_init(self):
        test = OneToOne(self.source_id, self.target_id, self.marker)
        print("String print:", test)
        tests = [                    
            ("Source Property", test.source, self.source_id),
            ("Target Property", test.target, self.target_id),
            ("Marker Property", test.marker, self.marker),
            ("Get with Source", test[self.source_id], self.target_id),
            ("Get with Target", test[self.target_id], self.source_id),
            ("Source contained", self.source_id in test, True),
            ("Not in", "fake" in test, False),
            ("Target contained", self.target_id in test, True),
        ]
        for name, result, expected in tests:
            with self.subTest(name=name):
                print(name + ":", result, expected)
                self.assertEqual(result, expected)
    
    def test_equality(self):
        marker1 = f"{self.marker}1"
        marker2 = f"{self.marker}2"
        test1 = OneToOne(self.source_id, self.target_id, marker1)
        test2 = OneToOne(self.source_id, self.target_id, marker1)
        test3 = OneToOne(self.source_id, self.target_id, marker2)
        with self.subTest("Equal relations, diff id"):
            self.assertTrue(test1 == test2)
            self.assertFalse(test1 != test2)
        with self.subTest("Unequal relation types"):
            self.assertFalse(test1 == test3)
            self.assertTrue(test1 != test3)
    
    def test_relation_set(self):
        test1 = OneToOne(self.source_id, self.target_id, self.marker)
        test2 = OneToOne(self.source_id, self.target_id, self.marker)
        test_set = set([test1, test2])
        print(test_set)
        self.assertEqual(len(test_set), 1)

class OneToManyBasicFunc(TestCase):
    
    def setUp(self):
        self.source_id = "source"
        self.target_id = "target"
        self.marker_prefix = "type" # Used as OneToMany level relation marker
        self.tindent = partial(indent, prefix="  ")
    
    def check_properties(self,
                         test: OneToMany,
                         center_id: Hashable,
                         source_ids: set[Hashable],
                         target_ids: set[Hashable],
                         center_value: set[Hashable],
                         many_to_markers: list[tuple[Hashable, Hashable]],
                         one_to_many_marker: Hashable,
                         source_centered: bool):
        print()
        print("String:")
        print(test)
        print(dict(test))
        print("getitem Tests:")
        for many, marker in many_to_markers:
            with self.subTest("Center and Marker to Many",
                              center=center_id, many=many, marker=marker):
                print(self.tindent(f"test[{center_id}, {marker}] ?= {many}"))
                self.assertEqual(test[center_id, marker], tuple([many]))
            with self.subTest("Many to Center", many=many, marker=marker):
                print(self.tindent(f"test[{many}] ?= {center_id}"))
                self.assertEqual(test[many], tuple([center_id]))
        with self.subTest("Center to Many", center=center_id, many=center_value):
            print(self.tindent(f"test[{center_id}] ?= {center_value}"))
            self.assertEqual(test[center_id], tuple(sorted(center_value)))
        print("Property Tests:")
        property_tests = [
            ("source:", test.source, tuple(sorted(source_ids))),
            ("target:", test.target, tuple(sorted(target_ids))),
            ("center:", test.center, center_id),
            ("marker:", test.marker, one_to_many_marker),
            ("source_centered:", test.source_centered, source_centered),
        ]
        for name, result, expected in property_tests:
            with self.subTest(name=name):
                print(self.tindent(f"{name} {result} ?= {expected}"))
                self.assertEqual(result, expected)
    
    def test_source_centered_init(self):
        relations = []
        many_to_markers = []
        target_ids = set()
        
        source = f"{self.source_id}"
        for i in range(0, 3):
            target = f"{self.target_id}{i}"
            marker = f"{self.marker_prefix}{i}"
            many_to_markers.append((target, marker))
            target_ids.add(target)
            relations.append(OneToOne(source, target, marker))
        
        test = OneToMany(relations, self.marker_prefix)
        self.check_properties(test,
                              center_id=source,
                              source_ids={source},
                              target_ids=target_ids,
                              center_value=target_ids,
                              many_to_markers=many_to_markers,
                              one_to_many_marker=self.marker_prefix,
                              source_centered=True)
    
    def test_target_centered_init(self):
        relations = []
        many_to_markers = []
        source_ids = set()
        
        target = f"{self.target_id}"
        for i in range(0, 3):
            source = f"{self.source_id}{i}"
            marker = f"{self.marker_prefix}{i}"
            many_to_markers.append((source, marker))
            source_ids.add(source)
            relations.append(OneToOne(source, target, marker))
        
        test = OneToMany(relations, self.marker_prefix)
        self.check_properties(test,
                              center_id=target,
                              source_ids=source_ids,
                              target_ids={target},
                              center_value=source_ids,
                              many_to_markers=many_to_markers,
                              one_to_many_marker=self.marker_prefix,
                              source_centered=False)
    
    def test_equality(self):
        sid = "source"
        tid = "target"
        m = "type"
        relations = []
        t_and_ms = []
        for i in range(0, 3):
            t_and_ms.append((tid + str(i), m + str(i)))
            relations.append(OneToOne(sid, *t_and_ms[-1]))
        test1 = OneToMany(relations, self.marker_prefix)
        test2 = OneToMany(relations, self.marker_prefix)
        test3 = OneToMany(relations[0:-1], self.marker_prefix)
        with self.subTest("Equal relations, diff id"):
            self.assertTrue(test1 == test2)
            self.assertFalse(test1 != test2)
        with self.subTest("Unequal relation types"):
            self.assertFalse(test1 == test3)
            self.assertTrue(test1 != test3)
    
    def test_relation_set(self):
        sid = "source"
        tid = "target"
        m = "type"
        relations = []
        t_and_ms = []
        for i in range(0, 3):
            t_and_ms.append((tid + str(i), m + str(i)))
            relations.append(OneToOne(sid, *t_and_ms[-1]))
        test1 = OneToMany(relations, self.marker_prefix)
        test2 = OneToMany(relations, self.marker_prefix)
        test_set = set([test1, test2])
        print(test_set)
        self.assertEqual(len(test_set), 1)