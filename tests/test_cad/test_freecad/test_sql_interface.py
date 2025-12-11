# from pathlib import Path
# from pprint import pp
# from contextlib import closing
# from uuid import uuid4
# from unittest import TestCase
# from xml.etree import ElementTree
# from zipfile import ZipFile

# import sqlite3

# from tests import sample_freecad

# from pancad.constants.config_paths import DATABASE
# from pancad.cad.freecad import sql_interface
# from pancad.cad.freecad.constants.archive_constants import Part, SubFile, Tag



# class OneOfEachSketchGeometrySQL(TestCase):
    # """Tests run on 'one_of_each_sketch_geometry.FCStd' to write its data to a 
    # fresh sql database
    # """
    
    # def setUp(self):
        # DATABASE.unlink(missing_ok=True) # Delete database
        # sample_dir = Path(sample_freecad.__file__).parent
        # self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
    
    # def tearDown(self):
        # DATABASE.unlink(missing_ok=True) # Delete database
    
    # def test_fcstd_to_sql(self):
        # sql_interface.fcstd_to_sql(self.path)
        # with closing(sqlite3.connect(DATABASE,
                                     # detect_types=sqlite3.PARSE_DECLTYPES)) as con:
            # line_segments = con.execute("SELECT * FROM FreecadObjectDependencies").fetchall()
        # print()
        # for ls in line_segments:
            # print(ls)
    
    # def test_write_data_to_sql(self):
        # sql_interface.ensure_tables(DATABASE)
        # columns = ('FileUid', 'Object', 'Dependency')
        # uid = uuid4()
        # data = [(str(uid), "TestChild", "TestParent")]
        # table = "FreecadObjectDependencies"
        # sql_interface.write_data_to_sql(DATABASE, table, columns, data)
        # with closing(sqlite3.connect(DATABASE)) as con:
            # test = con.execute(f"SELECT * FROM {table}").fetchall()
        # self.assertTupleEqual(test[0], data[0])
    
