from pathlib import Path
from pprint import pp
from unittest import TestCase
from xml.etree import ElementTree
from zipfile import ZipFile

from tests import sample_freecad

from pancad.cad.freecad import sql_interface
from pancad.cad.freecad.constants.archive_constants import Part, SubFile, Tag

class OneOfEachSketchGeometryParsing(TestCase):
    """Tests run on the 'one_of_each_sketch_geometry.FCStd' to parse data from 
    it
    """
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_parse_sketch_geometry(self):
        cols, vals = sql_interface.parse_sketch_geometry(self.tree,
                                                         Part.LINE_SEGMENT,
                                                         Tag.LINE_SEGMENT)
        print(cols)
        for v in vals: print(v)
    
    def test_parse_sketch_geometry_unrecognized(self):
        with self.assertRaises(sql_interface.UnsupportedGeometryType):
            cols, vals = sql_interface.parse_sketch_geometry(self.tree,
                                                             "FAKE_TYPE",
                                                             "FAKE_TAG")

class OneOfEachSketchGeometrySQL(TestCase):
    """Tests run on 'one_of_each_sketch_geometry.FCStd' to write its data to a 
    sql
    """
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
    
    def test_fcstd_to_sql(self):
        sql_interface.fcstd_to_sql(self.path)