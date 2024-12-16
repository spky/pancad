"""A module to provide functions for generating svg elements and writing svg files.

Uses Python's xml.etree.ElementTree XML API, see: https://docs.python.org/3/library/xml.etree.elementtree.html
"""

import xml.etree.ElementTree as ET
import svg_validators as sv

def xml_properties(properties: dict, delimiter: str = " ") -> str:
    """Returns the a string that is ready to be assigned to an xml 
    element. The delimiter parameter provides the option to have the 
    properties separated by a newline.
    
    :param properties: A dictionary full of key value pairs of the 
                        format 'property_name':'property_value'
    :returns: a string ready to be assigned to an xml property
    """
    props = []
    for prop in properties:
        props.append(prop + '="' + properties[prop] + '"')
    return delimiter.join(props)

def xml_declaration(properties: dict = {"version": "1.0", 
                                        "encoding": "UTF-8", 
                                        "standalone": "yes"},
                    delimiter: str = " ",
                    tail: str = "\n"
                    ) -> ET.Element:
    """Returns an processing instruction element to usually be placed 
    at the top of an xml file. The declaration will have a newline 
    appended to the end of it unless it an alternative is provided
    
    :param properties: A dictionary full of key value pairs of the 
                       format 'property_name':'property_value'
    :returns: A Processing Instruction Element with the given 
              properties as its text.
    """
    text = xml_properties(properties)
    element = ET.ProcessingInstruction("xml",text)
    element.tail = tail
    return element

def svg_top(svg_element: ET.Element, indent: str = "  ", declaration: ET.Element = None) -> ET.Element:
    """Returns a ET.Element that has the xml declaration at the top 
    and the svg right below it. Will create its own default 
    declaration if none are given, and will indent the svg 
    subelements by default.
    
    :param svg_element: an svg xml element
    :param indent: what to use as the indents between element levels
    :param declaration: a processing instruction xml element to 
                        prepend to the file
    :returns: The top element of an svg file assuming it has one svg element
    """
    if declaration is None:
        declaration = xml_declaration()
    top = ET.Element(None)
    top.append(declaration)
    if indent is not None:
        ET.indent(svg_element, indent)
    top.append(svg_element)
    return top

def svg_element_defaults(id_: str, width: str, height: str) -> dict:
    """Returns a dictionary of the default svg properties to then set to 
    an svg element.
    
    :param id_: the id of the svg element
    :param width: The width of the svg element
    :param height: The height of the svg element
    :returns: 
    """
    defaults = {
        "id": id_,
        "width": sv.length(width),
        "height": sv.length(height),
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:svg": "http://www.w3.org/2000/svg",
        #"viewBox": "0 0 " + sv.length(width) + " " + sv.length(height),
    }
    return defaults
    

def write_xml(filename: str, top_element: ET.Element) -> None:
    tree = ET.ElementTree(top_element)
    tree.write(filename)