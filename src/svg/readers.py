"""A module to provide functions for reading svg files

Uses Python's xml.etree.ElementTree XML API, see: https://docs.python.org/3/library/xml.etree.elementtree.html
SVG1.1 Specification: https://www.w3.org/TR/2011/REC-SVG11-20110816/
"""
from typing import TextIO
import xml.etree.ElementTree as ET
import re

import svg.validators as sv
import svg.parsers as sp
import svg.file as sf

xml_NameStartChar = ":A-Za-z_"
xml_NameChar = xml_NameStartChar + "\.0-9-"
xml_name_re = "[" + xml_NameStartChar + "][" + xml_NameChar + "]+"

def get_declaration(file: TextIO) -> dict:
    """Returns the settings states in the file's xml declaration. If there 
    is no declaration, returns None. It's likely that an equal sign inside 
    of a setting would cause an error, but right now that seems 
    unlikely to occur
    
    :param file: A python file object, assumed to be an xml/svg file
    :returns: A dictionary of the attributes and their values in the 
              declaration
    """
    position = file.tell()
    file.seek(0)
    text = file.read()
    match = re.match(r"<\?xml.*\?>", text, re.S)
    if match is not None:
        instruction = match.group()[5:-2]
        instruction = instruction.strip()
        tag_name_re_str = "".join([xml_name_re, "\s?=\s?"])
        tag_name_re = re.compile(tag_name_re_str, re.S)
        tags = tag_name_re.findall(instruction)
        tag_values = tag_name_re.split(instruction)
        settings = {"declaration": "real"}
        for i, tag_set in enumerate(tags):
            tag_name = re.search(xml_name_re, tag_set, re.S).group()
            settings[tag_name] = tag_values[i+1].strip()[1:-1]
    else:
        settings = None
    file.seek(position) # Reset file to what it was before the function
    return settings

def read_subelements(element: ET.Element) -> list[dict]:
    """Recursively (sorry) iterates through the given element tree to 
    and places each subelement in a dictionary with their associated 
    subelements
    :param tree: the tree to be upgraded
    :returns: an list of dictionaries with keys for "element" and 
              "subelements"
    """
    subelements = []
    for sub in list(element):
        sub_dict = {
            "element": sub,
            "subelements": read_subelements(sub),
        }
        subelements.append(sub_dict)
    return subelements

def read_element(element: ET.Element, tree: ET.ElementTree) -> dict:
    """Returns a dictionary containing the id, tag, parent, and properties 
    of the given element
    
    :param element: the child element
    :param tree: the tree that the child element resides in
    :returns: A dictionary containing the id, tag, parent, and properties 
    of the element
    """
    properties = dict(element.attrib)
    if "id" not in properties:
        raise ValueError("Element has no id attribute")
    parent_e = parent(element, tree)
    parent_id = parent_e.get("id") if parent_e is not None else None
    return {
        "id": properties.pop("id"),
        "tag": element.tag,
        "parent id": parent_id,
        "properties": properties,
    }

def parent(element: ET.Element, tree: ET.ElementTree) -> ET.Element:
    """Returns the parent element of the given element in the tree based 
    on the element's id. Will not work for elements without ids.
    
    :param element: the child element
    :param tree: the tree that the child element resides in
    :returns: the parent element
    """
    xpath = './/*[@id="' + element.get("id") + '"]/..'
    return tree.find(xpath)