"""A module to provide functions for generating svg elements and writing svg files.

Uses Python's xml.etree.ElementTree XML API, see: https://docs.python.org/3/library/xml.etree.elementtree.html



"""
import xml.etree.ElementTree as ET

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
    """
    
    """
    if declaration is None:
        declaration = xml_declaration()
    top = ET.Element(None)
    top.insert(0, declaration)
    ET.indent(svg_element, indent)
    top.append(svg_element)
    return top
    

def write_xml(filename: str, top_element: ET.Element) -> None:
    tree = ET.ElementTree(top_element)
    tree.write(filename)
    

"""
top = ET.Element(None)
dec = xml_declaration()
dec.set("poop","2.0")
top.insert(0, dec)
root = ET.Element("svg")
top.append(root)

layer = ET.Element("g")
path = ET.Element("path")

path.set("id", "path1")

root.append(layer)
layer.append(path)
#path1 = ET.SubElement(layer, "path")






tree = ET.ElementTree(top)
#ET.indent(tree, space="  ", level=0)
tree.write("test.xml")
"""