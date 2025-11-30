"""A module providing functions to interface with the FreeCAD portions of a 
pancad sqlite database.
"""

def table_columns(table: str) -> list[str]:
    with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)["sql_columns"][table]
    return list(config.keys())

def table_column_settings(table: str) -> list[str]:
    with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)["sql_columns"][table]
    return [f"{name} {type_}" for name, type_ in config.items()]

def write_sketch_geometry(database: str,
                          as_read_data: list[tuple[Any]],
                          file_uid: str) -> None:
    TABLE = "FreecadSketchGeometry"
    columns = table_column_settings(TABLE)
    data = [(file_uid, *values) for values in as_read_data]
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_constraints(database: str,
                      as_read_data: dict[str, list[dict]],
                      file_uid: UUID) -> None:
    TABLE = "FreecadSketchConstraints"
    columns = table_column_settings(TABLE)
    data = []
    for sketch, constraints in as_read_data.items():
        for i, constraint in enumerate(constraints):
            constraint.update(
                {"FileUid": file_uid, "SketchName": sketch, "ListIndex": i}
            )
            data.append(tuple(constraint[column]
                              for column in table_columns(TABLE)))
    
    with closing(sqlite3.connect(database)) as con:
        command = """CREATE TABLE IF NOT EXISTS %s(%s,
                  UNIQUE(FileUid, SketchName, ListIndex))"""
        con.execute(command % (TABLE, ", ".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_metadata(database: str, as_read_data: dict[str, Any]) -> None:
    """Writes FCStd file metadata to sql database. Only stores default FreeCAD 
    metadata.
    """
    TABLE = "FreecadDocumentMetadata"
    columns = table_column_settings(TABLE)
    data = [as_read_data[column] for column in table_columns(TABLE)]
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(Uid))"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.execute("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_objects_common(database: str,
                         as_read_data: list[tuple[Any]],
                         file_uid: UUID) -> None:
    """Writes the data that all FCStd objects share in common to sql database."""
    TABLE = "FreecadObjectsCommon"
    columns = table_column_settings(TABLE)
    data = [(file_uid,) + row for row in as_read_data]
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(FileUid, Id, Name))"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_object_dependencies(database: str,
                              as_read_data: dict[str, list[str]],
                              file_uid: str) -> None:
    TABLE = "FreecadObjectDependencies"
    columns = table_column_settings(TABLE)
    data = []
    for result, dependencies in as_read_data.items():
        data.extend([(file_uid, result, dep) for dep in set(dependencies)])
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()