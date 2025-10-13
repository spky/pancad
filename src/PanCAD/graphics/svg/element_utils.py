"""A module providing functions to change SVGElements. The functions in 
this module should only take ElementTree.Element or SVGElements and 
output SVGElement class elements or subclasses of that class.
"""

from xml.etree import ElementTree as ET

from pancad.graphics.svg import elements as se

def upgrade_element(element: ET.Element) -> se.SVGElement:
    """Subclasses the given element and all its subelements into 
    SVGElement classes and returns a reference to the element.
    
    :param element: A python ElementTree.Element
    :returns: The upgraded element, subclassed based on its tag
    """
    if element.tag in se.svg.tags:
        new = se.svg.from_element(element)
    elif element.tag in se.g.tags:
        new = se.g.from_element(element)
    elif element.tag in se.path.tags:
        new = se.path.from_element(element)
    elif element.tag in se.circle.tags:
        new = se.circle.from_element(element)
    elif element.tag in se.defs.tags:
        new = se.defs.from_element(element)
    else:
        new = se.SVGElement.from_element(element)
    for sub in list(element):
        new.append(upgrade_element(sub))
    element = new
    return element

def debug_print_all_elements(element: se.SVGElement) -> None:
    """Prints all the elements under a given svg element to the 
    screen with their tag, id, and class
    
    :param element: SVGElement to print the subelements of
    """
    for sub in element.iter():
        print("Tag: " + str(sub.tag)
              + " | " + str(sub.get("id"))
              + " | " + str(sub.__class__))