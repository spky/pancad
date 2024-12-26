"""A module to provide functions for generating svg elements and writing svg files.

Uses Python's xml.etree.ElementTree XML API, see: https://docs.python.org/3/library/xml.etree.elementtree.html
SVG1.1 Specification: https://www.w3.org/TR/2011/REC-SVG11-20110816/

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

def svg_top(svg_elements: list, indent: str = "  ", declaration: ET.Element = None) -> ET.Element:
    """Returns a ET.Element that has the xml declaration at the top 
    and the svg right below it. Will create its own default 
    declaration if none are given, and will indent the svg 
    subelements by default.
    
    :param svg_element: a list of svg xml elements
    :param indent: what to use as the indents between element levels
    :param declaration: a processing instruction xml element to 
                        prepend to the file
    :returns: The top element of an svg file assuming it has one svg element
    """
    if declaration is None:
        declaration = xml_declaration()
    top = ET.Element(None)
    top.append(declaration)
    for svg_element in svg_elements:
        if indent is not None:
            ET.indent(svg_element, indent)
        top.append(svg_element)
    return top

def svg_property_defaults(id_: str, width: str, height: str) -> dict:
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

def inkscape_svg_property_defaults(document_name: str) -> dict:
    """Returns a dictionary of the default inkscape properties that 
    it adds to an svg element.
    
    :param document_name: the name of the inkscape document
    :returns: dictionary of default inkscape properties
    """
    defaults = {
        "xmlns:inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "xmlns:sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "sodipodi:docname": document_name,
    }
    return defaults

def make_element(tag:str, property_dicts: list = None) -> ET.Element:
    """Returns a generic element with the specified tag and 
    properties. In the event of duplicate properties, the 
    dictionaries towards the end of the list are prioritized.
    
    :param tag: element tag name
    :param: property_dicts: a list of dictionaries with the tag's properties
    :returns: an xml element with the specified tag and properties
    """
    properties = {}
    if property_dicts is not None:
        for dict_ in property_dicts:
            properties = properties | dict_
    element = ET.Element(tag)
    for prop in properties:
        element.set(prop, properties[prop])
    return element

def make_svg_element(
        id_: str, width: str, height: str, 
        property_dicts: list = None) -> ET.Element:
    """Returns an element with svg as its tag. Assigns the properties 
    in the given dictionaries to the element. 
    
    :param property_dicts: a list of dictionaries with properties to 
                           assign to the element
    :returns: an svg element with assigned properties
    """
    properties = [{
            "xmlns": "http://www.w3.org/2000/svg",
            "xmlns:svg": "http://www.w3.org/2000/svg",
            "width": sv.length(width),
            "height": sv.length(height),
            "viewBox": " ".join([
                               "0",
                               "0",
                               str(sv.length_value(width)),
                               str(sv.length_value(height)),
                           ]),
            "id": id_,
    }]
    if property_dicts is not None:
        properties = properties + property_dicts
    return make_element("svg", properties)

def make_g_element(id_: str, property_dicts: list = None) -> ET.Element:
    """Returns a 'g' (group) tagged element with at least the id filled 
    out. Will also assign additional properties from the dictionaries in 
    property_dicts if it is provided
    
    :param id_: the id of the element
    :param property_dicts: the additional properties of the group in 
                           dictionaries
    """
    properties = [{
        "id": id_,
    }]
    if property_dicts is not None:
        properties = properties + property_dicts
    return make_element("g", properties)

def make_path_element(
        id_: str, style: str, d: str,
        property_dicts: list = None) -> ET.Element:
    """Returns a 'path' tagged element with at least the id, style, 
    and d properties filled out. Will also assign additional 
    properties from the dictionaries in property_dicts if it is 
    provided.
    
    :param id_: the id of the element
    :param style: the svg style of the path
    :param d: the path data of the path
    :property_dicts: the additional properties of the path in dictionaries
    :returns: a path element with the properties above assigned to it
    """
    properties = [{
        "style": style,
        "d": d,
        "id": id_,
    }]
    if property_dicts is not None:
        properties = properties + property_dicts
    return make_element("path", properties)

def make_circle_element(
        id_: str, style: str, center_xy: list, radius: str,
        property_dicts: list = None):
    """Returns a 'circle' tagged element with at least the id, style, 
    center location, and radius properties filled out. Will also assign 
    additional properties from the dictionaries in property_dicts if it is 
    provided.
    
    :param id_: the id of the element
    :param style: the svg style of the circle
    :param center_xy: the location of the circle center in list form 
                      [x, y] where x and y are length strings
    :param radius: the radius of the circle
    :property_dicts: the additional properties of the circle in dictionaries
    :returns: a circle element with the properties above assigned to it
    """
    properties = [{
        "style": style,
        "cx": str(sv.length_value(center_xy[0])),
        "cy": str(sv.length_value(center_xy[1])),
        "r": str(sv.length_value(radius)),
        "id": id_,
    }]
    if property_dicts is not None:
        properties = properties + property_dicts
    return make_element("circle", properties)

def write_xml(filepath: str, top_element: ET.Element) -> None:
    """Writes the given element to an xml file
    
    :param filepath: the filepath of the new file
    :param top_element: the element to be written
    """
    
    tree = ET.ElementTree(top_element)
    tree.write(filepath)