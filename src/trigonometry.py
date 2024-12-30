"""Provides trigonometric functions to help translate geometry between formats
"""

import math
import numpy as np
from numpy.linalg import norm

def point_2d(point: list[float | int]) -> np.ndarray:
    """Returns a 2x1 numpy array made from an [x, y] list coordinate. 
    Can also be used to make 2x1 vectors
    
    :param point: coordinate list of format [x, y]
    :returns: a 2x1 numpy representation
    """
    return np.array([[point[0]],[point[1]]])

def point_line_angle(point_a: np.ndarray, point_b: np.ndarray,
                     decimals: int = 6, radians: bool = True):
    """Returns the angle of the line created between two 2D [x, y] points
    
    :param point_a: first point's x and y coordinates
    :param point_b: second point's x and y coordinates
    :param decimals: the number of decimals the output is rounded to
    :param radians: returns in radians if left true, degrees if false
    :returns: the angle of the line between points a and b
    """
    difference = point_b - point_a
    angle = math.atan2(difference[1][0], difference[0][0])
    
    if radians:
        return round(angle, decimals)
    else:
        return math.degrees(angle)

def three_point_angle(point_1: np.ndarray, point_2: np.ndarray,
                      root_point: np.ndarray, decimals: int = 6) -> float:
    """Returns the angle between the lines created by the root point 
    and points 1 and 2
    
    :param point_1: first point's coordinate
    :param point_2: second point's coordinate
    :param root_point: the line intersection point
    :returns: the angle between the two lines in radians
    """
    u = point_1 - root_point
    v = point_2 - root_point
    return angle_between_vectors_2d(u, v, decimals)
    

def angle_between_vectors_2d(u: np.ndarray, v: np.ndarray,
                             decimals: int = 6, radians: bool = True) -> float:
    """Returns the angle between two 2d vectors represented as numpy 
    arrays. WARNING: degrees hardcoded to 2 decimals
    
    :param u: 1-D 2x1 vector u
    :param v: 1-D 2x1 vector v
    :returns: the angle between vectors a and b
    """
    u = u.reshape(2)
    v = v.reshape(2)
    normalized_dot = np.dot(u, v)/(norm(u)*norm(v))
    
    if (u[0]*v[1] - u[1]*v[0]) >= 0:
        # A zero result is assumed to have an implicit positive sign
        angle = math.acos(normalized_dot)
    else:
        angle = -math.acos(normalized_dot)
    if radians:
        return round(angle, decimals)
    else:
        # WARNING: degrees hardcoded to 2 decimals
        return round(math.degrees(angle), 2)

def distance_2d(point_a: np.ndarray, point_b: np.ndarray,
                decimals: int = 6) -> float:
    """Returns the distance between two 2D [x, y] points
    
    :param point_a: first point's x and y coordinates
    :param point_b: second point's x and y coordinates
    :param decimals: the number of decimals the output is rounded to
    :returns: the distance between points a and b
    """
    x0 = point_a[0][0]
    y0 = point_a[1][0]
    x1 = point_b[0][0]
    y1 = point_b[1][0]
    distance = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    return round(distance, decimals)

def round_array(array: np.ndarray, decimals: int) -> np.ndarray:
    """Returns a numpy array with each element rounded to the 
    specified number of decimals
    
    :param array: the array to be rounded
    :param decimals: how many decimals to round to
    """
    rounder = lambda x: np.round(x, decimals)
    return rounder(array)

def rotation_2d(angle: float, decimals: int = None) -> np.ndarray:
    """Returns a 2d numpy rotation matrix
    
    :param angle: Rotation matrix angle in radians
    :param decimals: the number of decimals the output elements are 
                     rounded to
    :returns: Rotation matrix
    """
    matrix = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle), np.cos(angle)]
    ])
    if decimals is not None:
        matrix = round_array(matrix, decimals)
        #rounder = lambda x: np.round(x, decimals)
        #matrix = rounder(matrix)
    return matrix

def midpoint_2d(point_1: np.ndarray, point_2: np.ndarray) -> np.ndarray:
    """Returns the midpoint between two points as a 2x1 numpy array
    
    :param point_1: First point as an [x, y] numpy array
    :param point_2: Second point as an [x, y] numpy array
    :returns: midpoint between points 1 and 2
    """
    return (point_1 + point_2)/2

def ellipse_point(center_point: np.ndarray,
                  major_radius: float, minor_radius: float,
                  major_axis_angle: float, angle: float,
                  decimals: int = 6) -> np.ndarray:
    """Returns the point at the specified angle centered at the 
    ellipse center and wrt the x-axis on the given ellipse.
    
    :param center_point: the center point of the ellipse
    :param major_radius: the major axis radius of the ellipse
    :param minor_radius: the minor axis radius of the ellipse
    :param major_axis_angle: the ellipse's major axis angle wrt the 
                             x-axis in radians
    :param angle: the angle that the desired point is at on the 
                  ellipse in radians
    :param decimals: the number of decimals the output is rounded to
    :returns: the coordinate of the ellipse point
    """
    a = major_radius
    b = minor_radius
    angle = angle % np.pi if abs(angle) > np.pi else angle
    t = round(angle, decimals)
    major_axis_rotation = rotation_2d(major_axis_angle)
    if t == 0:
        x = a
        y = 0
    elif abs(t) == round(np.pi, decimals):
        x = -a
        y = 0
    elif t == round(np.pi/2, decimals):
        x = 0
        y = b
    elif t == round(-np.pi/2, decimals):
        x = 0
        y = -b
    else:
        x = (a * b)/math.sqrt(b**2 + a**2 * math.tan(t)**2)
        y = (a * b)/math.sqrt(b**2 / math.tan(t)**2 + a**2)
        x = x if t >= -np.pi/2 and t <= np.pi/2 else -x
        y = y if t >= 0 and t <= np.pi else -y
    unrotated_ellipse_pt = point_2d([x, y])
    ellipse_pt = major_axis_rotation @ unrotated_ellipse_pt + center_point
    return round_array(ellipse_pt, decimals)

def circle_point(center_point: np.ndarray, radius: float, angle: float,
                 decimals: int = 6) -> np.ndarray:
    """Returns the point at the specified angle centered at the 
    circle center and wrt the x-axis on the given circle.
    
    :param center_point: the center point of the circle
    :param radius: the radius of the circle
    :param angle: the angle that the desired point is at on the 
                  circle in radians
    :param decimals: the number of decimals the output is rounded to
    :returns: the coordinate of the circle point
    """
    return ellipse_point(center_point, radius, radius, 0, angle, decimals)

def elliptical_arc_endpoint_to_center(
        point_1: np.ndarray, point_2: np.ndarray,
        large_arc_flag: bool, sweep_flag: bool,
        major_radius: float, minor_radius: float, major_axis_angle: float,
        decimals: int = 6) -> list[np.ndarray, float, float]:
    """Returns the center coordinate and angles [cx, cy, theta_1, 
    delta_theta] of an arc. Method based on  of section F.6.5 of the 
    SVG 1.1 specification. Keep in mind that SVGs are effectively 
    'upside down' since the origin is in the top left with positive y 
    down and angles are positive in the clockwise direction!
    
    :param point_1: The first arc point coordinate [x1, y1]
    :param point_2: The second arc point coordinate [x2, y2]
    :param large_arc_flag: If true the arc sweep greater than or 
                           equal to 180 degrees is chosen
    :param sweep_flag: If true than the positive angle direction arc 
                       is chosen
    :param major_radius: the semi-major axis radius
    :param minor_radius: the semi-minor axis radius
    :param major_axis_angle: angle from the x-axis to the major axis 
                             in radians
    :param decimals:  the number of decimals the output is rounded to
    :returns: The arc's center point [cx, cy], the first point's 
              angle, and the arc's extent angle
    """
    fa = large_arc_flag
    fs = sweep_flag 
    rx = major_radius
    ry = minor_radius
    theta = major_axis_angle
    
    rotation = rotation_2d(-theta)
    midpoint = midpoint_2d(point_1, point_2)
    pt1_p = rotation @ (point_1 - midpoint)
    x1p, y1p = pt1_p[0, 0], pt1_p[1, 0]
    step_2_term_1_numerator = (rx**2 * ry**2
                               - rx**2 * y1p**2
                               - ry**2 * x1p**2)
    step_2_term_1_denominator = (rx**2 * y1p**2
                                 + ry**2 * x1p**2)
    step_2_term_1 = math.sqrt(step_2_term_1_numerator
                              / step_2_term_1_denominator)
    if not fa ^ fs:
        step_2_term_1 = -step_2_term_1
    step_2_term_2 = np.array([[rx * y1p / ry], [-ry * x1p / rx]])
    center_pt_p = step_2_term_1 * step_2_term_2
    
    back_rotation = rotation_2d(theta)
    center_pt = (back_rotation @ center_pt_p) + midpoint
    
    rx_ry = np.array([[rx],[ry]])
    theta_1 = angle_between_vectors_2d(
        np.array([[1],[0]]), 
        pt1_p - center_pt_p
    )
    
    delta_theta = angle_between_vectors_2d(
        pt1_p - center_pt_p,
        -pt1_p - center_pt_p
    )
    delta_theta = delta_theta % (2*np.pi)
    if not sweep_flag and delta_theta > 0:
        delta_theta = delta_theta - 2*np.pi
    elif sweep_flag and delta_theta < 0:
        delta_theta = delta_theta + 2*np.pi
    
    return [round_array(center_pt, decimals),
            round(theta_1, decimals),
            round(delta_theta, decimals)]

def circle_arc_endpoint_to_center(
        point_1: np.ndarray, point_2: np.ndarray,
        large_arc_flag: bool, sweep_flag: bool, radius: float,
        decimals: int = 6) -> list[np.ndarray, float, float]:
    """Returns the center coordinate and angles [cx, cy, theta_1, 
    delta_theta] of an arc. Uses the 
    elliptical_arc_endpoint_to_center function with the inputs set 
    for a circle
    
    :param point_1: The first arc point coordinate [x1, y1]
    :param point_2: The second arc point coordinate [x2, y2]
    :param large_arc_flag: If true the arc sweep greater than or 
                           equal to 180 degrees is chosen
    :param sweep_flag: If true than the positive angle direction arc 
                       is chosen
    :param radius: the arc's radius
    :returns: The arc's center point [cx, cy], the first point's 
              angle, and the arc's extent angle
    """
    return elliptical_arc_endpoint_to_center(point_1, point_2,
                                             large_arc_flag, sweep_flag,
                                             radius, radius, 0, decimals)

def elliptical_arc_center_to_endpoint(
        center_point: np.ndarray, major_radius: float,
        minor_radius: float, major_axis_angle: float,
        point_1_angle: float, sweep_angle: float,
        decimals: int = 6) -> list:
    """Returns a list of arc end points and flag values. Method based 
    on section F.6.4 of the SVG 1.1 specification. The SVG 1.1 
    equation F.6.4.1 is incorrect (or at least unclear) since they 
    are assuming you have access to the eccentric anomaly, so the 
    ellipse_point function uses a separately derived equation to 
    determine the point coordinates
    
    :param center_point: Center point of the arc's ellipse
    :param major_radius: the semi-major axis radius
    :param minor_radius: the semi-minor axis radius
    :param major_axis_angle: angle from the x-axis to the major axis 
                             in radians
    :param point_1_angle: the angle that the first arc point is at on the 
                          ellipse in radians
    :param sweep_angle: the between the start and end points of the arc
    :param decimals:  the number of decimals the output is rounded to
    :returns: The start point coordinate, end point coordinate, the 
              svg 1.1 large arc flag, and the svg 1.1 sweep flag
    """
    pt1 = ellipse_point(center_point, major_radius, minor_radius,
                        major_axis_angle, point_1_angle,
                        decimals)
    pt2 = ellipse_point(center_point, major_radius, minor_radius,
                        major_axis_angle, point_1_angle + sweep_angle,
                        decimals)
    fa = True if abs(sweep_angle) > np.pi else False
    fs = True if sweep_angle > 0 else False
    return [pt1, pt2, fa, fs]

def circle_arc_center_to_endpoint(
        center_point: np.ndarray, radius: float,
        point_1_angle: float, sweep_angle: float, decimals: int = 6) -> list:
    """Returns a list of arc end points and flag values. Uses the 
    elliptical_arc_center_to_endpoint function with the inputs set 
    for a circle
    
    :param center_point: Center point of the arc's circle
    :param radius: the semi-major axis radius
    :param point_1_angle: the angle that the first arc point is at on the 
                          circle in radians
    :param sweep_angle: the between the start and end points of the arc
    :param decimals:  the number of decimals the output is rounded to
    :returns: The start point coordinate, end point coordinate, the 
              svg 1.1 large arc flag, and the svg 1.1 sweep flag
    """
    return elliptical_arc_center_to_endpoint(center_point, radius, radius,
                                             0, point_1_angle, sweep_angle,
                                             decimals)

