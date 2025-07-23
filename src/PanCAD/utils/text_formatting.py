"""A module providing functions for common string formatting operations. 
Originally intended for command line reports/summaries.
"""

def get_table_string(data: list[dict],
                     column_map: dict=None,
                     column_delimiter: str="  ") -> str:
    """Returns the dictionary data in tabular format, using the keys as column
    titles.
    
    :param data: A list of dictionaries, each with the same set of keys.
    :param column_map: A dictionary with renamed column labels as keys and the 
        original keys in data as their values. Example: 'index': 'Index'.
    :param column_delimiter: The string to place between columns.
    """
    string_rows = []
    if column_map is None:
        # If no column map is given, the data keys are used as the columns
        column_map = {key: key for key in data[0]}
    
    for column, key in column_map.items():
        column_width = len(column)
        rows = [column]
        rows.extend([info[key] for info in data])
        
        lengths = list(
            map(lambda s: len(str(s)), rows)
        )
        if max(lengths) > column_width:
            # Check if any of the rows are longer than the column label
            column_width = max(lengths)
        
        rows = ["{0: <{1}}".format(str(s), column_width) for s in rows]
        if len(string_rows) == 0:
            string_rows = rows
        else:
            for i, row in enumerate(rows):
                string_rows[i] = column_delimiter.join([string_rows[i], row])
    return "\n".join(string_rows)