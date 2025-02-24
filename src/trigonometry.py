"""A module to provide trigonometric functions that translate geometry 
between formats.
"""

import math
import numpy as np

def point_2d(point: list[float | int]) -> np.ndarray:
    """Returns a 2x1 numpy array made from an [x, y] list coordinate. 
    Can also be used to make 2x1 vectors. Will not do anything if it is 
    passed a numpy array that is already 2 elements.
    
    :param point: Coordinate list of format [x, y]
    :returns: A 2x1 numpy representation
    """
    if isinstance(point, list):
        point_length = len(point)
        if point_length == 2:
            return np.array([[point[0]],[point[1]]])
        else:
            raise ValueError(f"Must be 2 elements long, given: {point_length}")
    elif isinstance(point, np.ndarray):
        if point.size == 2:
            return point
        else:
            raise ValueError(f"Must be 2 long, given {point.size}")
    else:
        raise ValueError("Unrecognized instance type")

def pt2list(point: np.ndarray) -> list:
    """Returns a 2 element list from a 2x1 numpy array made of xy 
    coordinates. Will not do anything if passed a list that is already 
    just 2 elements.
    
    :param point: A 2x1 numpy array
    :returns: A 2 element list
    """
    if isinstance(point, list):
        point_length = len(point)
        if point_length == 2:
            return point
        else:
            raise ValueError(f"Must be 2 long, given {point_length}")
    elif isinstance(point, np.ndarray):
        if point.size == 2:
            return [float(point[0][0]), float(point[1][0])]
        else:
            raise ValueError(f"Must be 2 long, given {point.size}")
    else:
        raise ValueError("Unrecognized instance type")

def point_line_angle(point_a: np.ndarray, point_b: np.ndarray,
                     decimals: int = 6, radians: bool = True):
    """Returns the angle of the line created between two 2D [x, y] points.
    
    :param point_a: First point's x and y coordinates
    :param point_b: Second point's x and y coordinates
    :param decimals: The number of decimals to round to, defaults to 6
    :param radians: Returns in radians if left true, degrees if false
    :returns: The angle of the line between points a and b
    """
    difference = point_b - point_a
    angle = math.atan2(difference[1][0], difference[0][0])
    
    if radians:
        return round(angle, decimals)
    else:
        return math.degrees(angle)

def three_point_angle(point_1: np.ndarray, point_2: np.ndarray,
                      root_point: np.ndarray, decimals: int = 6) -> float:
    """Returns the angle between the lines created by the root<->1 and root<->2.
    
    :param point_1: First point's coordinate
    :param point_2: Second point's coordinate
    :param root_point: The line intersection point
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The angle between the two lines in radians
    """
    u = point_1 - root_point
    v = point_2 - root_point
    return angle_between_vectors_2d(u, v, decimals)

def angle_between_vectors_2d(u: np.ndarray, v: np.ndarray,
                             decimals: int = 6, radians: bool = True) -> float:
    """Returns the angle between two 2d vectors represented as numpy 
    arrays. WARNING: Degrees return option rounding hardcoded to 2 decimals.
    
    :param u: A 1-D 2x1 vector u
    :param v: A 1-D 2x1 vector v
    :param decimals: The number of decimals to round to, defaults to 6
    :param radians: Determines return type degrees or radians, defaults radians
    :returns: The angle between vectors a and b
    """
    u = u.reshape(2)
    v = v.reshape(2)
    normalized_dot = np.dot(u, v)/(np.linalg.norm(u)*np.linalg.norm(v))
    
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
    """Returns the distance between two 2D [x, y] points.
    
    :param point_a: First point's x and y coordinates
    :param point_b: Second point's x and y coordinates
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The distance between points a and b
    """
    x0 = point_a[0][0]
    y0 = point_a[1][0]
    x1 = point_b[0][0]
    y1 = point_b[1][0]
    distance = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    return round(distance, decimals)

def round_array(array: np.ndarray, decimals: int) -> np.ndarray:
    """Returns a numpy array with each element rounded to the 
    specified number of decimals.
    
    :param array: The array to be rounded
    :param decimals: The number of decimals to round to
    :returns: The array with each element rounded to the number of decimals
    """
    rounder = lambda x: np.round(x, decimals)
    return rounder(array)

def rotation_2d(angle: float, decimals: int = None) -> np.ndarray:
    """Returns a 2d numpy rotation matrix.
    
    :param angle: Rotation matrix angle in radians
    :param decimals: The number of decimals the output elements are 
                     rounded to, defaults to None (no rounding)
    :returns: Rotation matrix to achieve the angle
    """
    matrix = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle), np.cos(angle)]
    ])
    if decimals is not None:
        matrix = round_array(matrix, decimals)
    return matrix

def midpoint_2d(point_1: np.ndarray, point_2: np.ndarray) -> np.ndarray:
    """Returns the midpoint between two points as a 2x1 numpy array.
    
    :param point_1: The first point as an [x, y] numpy array
    :param point_2: The second point as an [x, y] numpy array
    :returns: The midpoint between points 1 and 2
    """
    return (point_1 + point_2)/2

def ellipse_point(center_point: np.ndarray,
                  major_radius: float, minor_radius: float,
                  major_axis_angle: float, angle: float,
                  decimals: int = 6) -> np.ndarray:
    """Returns the point at the specified angle centered at the ellipse 
    center and wrt the x-axis on the given ellipse.
    
    :param center_point: The center point of the ellipse
    :param major_radius: The major axis radius of the ellipse
    :param minor_radius: The minor axis radius of the ellipse
    :param major_axis_angle: The ellipse's major axis angle wrt the 
                             x-axis in radians
    :param angle: The angle that the desired point is at on the 
                  ellipse in radians
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The coordinate of the ellipse point
    """
    a = major_radius
    b = minor_radius
    angle = angle_mod(angle) if abs(angle) > (2*np.pi) else angle
    t = round(angle, decimals)
    major_axis_rotation = rotation_2d(major_axis_angle)
    # E is 'Eccentric Anomaly'
    E = math.atan2(a * math.sin(t), b * math.cos(t))
    x = a * math.cos(E)
    y = b * math.sin(E)
    unrotated_ellipse_pt = point_2d([x, y])
    ellipse_pt = major_axis_rotation @ unrotated_ellipse_pt + center_point
    return round_array(ellipse_pt, decimals)

def circle_point(center_point: np.ndarray, radius: float, angle: float,
                 decimals: int = 6) -> np.ndarray:
    """Returns the point at the specified angle centered at the 
    circle center and wrt the x-axis on the given circle.
    
    :param center_point: The center point of the circle
    :param radius: The radius of the circle
    :param angle: The angle that the desired point is at on the 
                  circle in radians
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The coordinate of the circle point
    """
    return ellipse_point(center_point, radius, radius, 0, angle, decimals)

def elliptical_arc_endpoint_to_center(
        start: np.ndarray, end: np.ndarray,
        large_arc_flag: bool, sweep_flag: bool,
        major_radius: float, minor_radius: float, major_axis_angle: float,
        decimals: int = 6
    ) -> list[np.ndarray, float, float]:
    """Returns the center coordinate and angles [cx, cy, theta_1, 
    delta_theta] of an arc. Method based on  of section F.6.5 of the 
    SVG 1.1 specification. Keep in mind that SVGs are effectively 
    'upside down' since the origin is in the top left with positive y 
    down and angles are positive in the clockwise direction!
    
    :param start: The first arc point coordinate [x1, y1]
    :param end: The second arc point coordinate [x2, y2]
    :param large_arc_flag: If true the arc sweep greater than or 
                           equal to 180 degrees is chosen
    :param sweep_flag: If true than the positive angle direction arc 
                       is chosen
    :param major_radius: The semi-major axis radius
    :param minor_radius: The semi-minor axis radius
    :param major_axis_angle: angle from the x-axis to the major axis 
                             in radians
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The arc's center point [cx, cy], the first point's 
              angle, and the arc's sweep angle
    """
    fa = large_arc_flag
    fs = sweep_flag 
    rx = major_radius
    ry = minor_radius
    theta = major_axis_angle
    rotation = rotation_2d(-theta)
    midpoint = midpoint_2d(start, end)
    pt1_p = rotation @ (start - midpoint)
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
    delta_theta = angle_mod(delta_theta)
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
        decimals: int = 6
    ) -> list[np.ndarray, float, float]:
    """Returns the center coordinate and angles [cx, cy, theta_1, 
    delta_theta] of an arc. Uses the elliptical_arc_endpoint_to_center 
    function with the inputs set for a circle.
    
    :param point_1: The first arc point coordinate [x1, y1]
    :param point_2: The second arc point coordinate [x2, y2]
    :param large_arc_flag: If true the arc sweep greater than or 
                           equal to 180 degrees is chosen
    :param sweep_flag: If true than the positive angle direction arc 
                       is chosen
    :param radius: the arc's radius
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The arc's center point [cx, cy], the first point's 
              angle, and the arc's extent angle
    """
    return elliptical_arc_endpoint_to_center(point_1, point_2,
                                             large_arc_flag, sweep_flag,
                                             radius, radius, 0, decimals)

def elliptical_arc_center_to_endpoint(
        center_point: np.ndarray, major_radius: float, minor_radius: float,
        major_axis_angle: float, point_1_angle: float, sweep_angle: float,
        decimals: int = 6
    ) -> list:
    """Returns a list of arc end points and flag values. Method based 
    on section F.6.4 of the SVG 1.1 specification. The SVG 1.1 
    equation F.6.4.1 is incorrect (or at least unclear) since they 
    are assuming you have access to the eccentric anomaly, so the 
    ellipse_point function uses a separately derived equation to 
    determine the point coordinates.
    
    :param center_point: Center point of the arc's ellipse
    :param major_radius: the semi-major axis radius
    :param minor_radius: the semi-minor axis radius
    :param major_axis_angle: angle from the x-axis to the major axis 
                             in radians
    :param point_1_angle: the angle that the first arc point is at on the 
                          ellipse in radians
    :param sweep_angle: the between the start and end points of the arc
    :param decimals: The number of decimals to round to, defaults to 6
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
        point_1_angle: float, sweep_angle: float,
        decimals: int = 6
    ) -> list:
    """Returns a list of arc end points and flag values. Uses the 
    elliptical_arc_center_to_endpoint function with the inputs set 
    for a circle.
    
    :param center_point: Center point of the arc's circle
    :param radius: the semi-major axis radius
    :param point_1_angle: the angle that the first arc point is at on the 
                          circle in radians
    :param sweep_angle: the between the start and end points of the arc
    :param decimals: The number of decimals to round to, defaults to 6
    :returns: The start point coordinate, end point coordinate, the 
              svg 1.1 large arc flag, and the svg 1.1 sweep flag
    """
    major_axis_angle = 0
    return elliptical_arc_center_to_endpoint(
        center_point, radius, radius, major_axis_angle,
        point_1_angle, sweep_angle, decimals
    )

def line_fit_box(start: np.ndarray,
                 end: np.ndarray) -> list[np.ndarray, np.ndarray]:
    """Returns the corners of the smallest box that the line would 
    fit into. Useful for sizing graphics.
    
    :param start: The start point of the line
    :param end: The end point of the line
    :returns: a list of the minimum corner and the maximum corner 
              points of the smallest box that would fit the line
    """
    min_x = min(start[0][0], end[0][0])
    min_y = min(start[1][0], end[1][0])
    max_x = max(start[0][0], end[0][0])
    max_y = max(start[1][0], end[1][0])
    return [point_2d([min_x, min_y]), point_2d([max_x, max_y])]

def circle_fit_box(center_point: np.ndarray,
                   radius: float) -> list[np.ndarray, np.ndarray]:
    """Returns the corners of the smallest box that the circle would fit into.
    Useful for sizing graphics.
    
    :param center_point: The center point of the circle
    :param radius: The radius of the circle
    :returns: a list of the minimum corner and the maximum corner 
              points of the smallest box that would fit the circle
    """
    v = [(center_point + point_2d([0, radius])).reshape(2),
         (center_point + point_2d([0, -radius])).reshape(2),
         (center_point + point_2d([radius, 0])).reshape(2),
         (center_point + point_2d([-radius, 0])).reshape(2)]
    min_x = min(v[0][0], v[1][0], v[2][0], v[3][0])
    max_x = max(v[0][0], v[1][0], v[2][0], v[3][0])
    min_y = min(v[0][1], v[1][1], v[2][1], v[3][1])
    max_y = max(v[0][1], v[1][1], v[2][1], v[3][1])
    return [point_2d([min_x, min_y]), point_2d([max_x, max_y])]

def ellipse_fit_box(
        center_point: np.ndarray, major_radius: float, minor_radius: float,
        major_axis_angle: float
    ) -> list[np.ndarray, np.ndarray]:
    """Returns the corners of the smallest box that the ellipse would fit into. 
    Useful for sizing graphics.
    
    :param center_point: The center point of the circle
    :param major_radius: The major axis radius of the ellipse
    :param minor_radius: The minor axis radius of the ellipse
    :param major_axis_angle: The angle between the coordinate system's 
                             x axis and the ellipse's major_axis
    :returns: A list of the minimum corner and the maximum corner 
              points of the smallest box that would fit the circle
    """
    left_right_offset = math.sqrt(
        major_radius**2 * math.cos(major_axis_angle)**2
        + minor_radius**2 * math.sin(major_axis_angle)**2)
    up_down_offset = math.sqrt(
        minor_radius**2 * math.cos(major_axis_angle)**2
        + major_radius**2 * math.sin(major_axis_angle)**2)
    
    v = [(center_point + point_2d([0, up_down_offset])).reshape(2),
         (center_point + point_2d([0, -up_down_offset])).reshape(2),
         (center_point + point_2d([left_right_offset, 0])).reshape(2),
         (center_point + point_2d([-left_right_offset, 0])).reshape(2)]
    min_x = min(v[0][0], v[1][0], v[2][0], v[3][0])
    max_x = max(v[0][0], v[1][0], v[2][0], v[3][0])
    min_y = min(v[0][1], v[1][1], v[2][1], v[3][1])
    max_y = max(v[0][1], v[1][1], v[2][1], v[3][1])
    return [point_2d([min_x, min_y]), point_2d([max_x, max_y])]

def angle_mod(angle: float) -> float:
    """Returns the angle bounded from -2pi to +2pi since python's modulo 
    operator by default always returns the divisor's sign, which is 
    different than other programming languages like C and C++.
    
    :param angle: The angle in radians
    :returns: The equivalent angle bounded between -2pi and +2pi
    """
    if angle >= 0:
        return angle % (2*np.pi)
    else:
        return angle % (-2*np.pi)

def positive_angle(angle: float) -> float:
    """Returns the positive representation of an angle
    
    :param angle: The angle in radians
    :returns: The angle bounded from 0 to 2pi
    """
    if angle >= 0:
        return angle_mod(angle)
    else:
        return angle_mod(angle) + 2*np.pi

def elliptical_arc_fit_box(
        center_point: np.ndarray, major_radius: float, minor_radius: float,
        major_axis_angle: float, point_1_angle: float, sweep_angle: float
    ) -> list[np.ndarray, np.ndarray]:
    """Returns the corners of the smallest box that the elliptical arc 
    would fit into. Useful for sizing graphics.
    
    :param center_point: The center point of the ellipse
    :param major_radius: The major axis radius of the ellipse
    :param minor_radius: The minor axis radius of the ellipse
    :param major_axis_angle: The angle between the coordinate system's 
                             x axis and the ellipse's major_axis
    :param point_1_angle: The angle from the major axis of the ellipse to 
                          the arc's first point, in radians
    :param sweep_angle: The angle from the first point to the second point in 
                        radians
    :returns: Min and max corner points of the smallest box that would fit the 
              elliptical arc
    """
    start_angle = positive_angle(point_1_angle)
    end_angle = positive_angle(start_angle + angle_mod(sweep_angle))
    
    if sweep_angle > 0:
        cw_angle = start_angle
        ccw_angle = end_angle
    else:
        cw_angle = end_angle
        ccw_angle = start_angle
    sweep = positive_angle(ccw_angle - cw_angle)
    # E is 'Eccentric Anomaly'. A huge number of guides online mix up the 
    # angle between the major axis and the ellipse point with E!
    max_Es = []
    max_Es.append(positive_angle(
        -math.atan2(minor_radius * math.sin(major_axis_angle),
                    major_radius * math.cos(major_axis_angle))
    ))
    max_Es.append(positive_angle(np.pi + max_Es[-1]))
    max_Es.append(positive_angle(
        math.atan2(minor_radius * math.cos(major_axis_angle),
                   major_radius * math.sin(major_axis_angle))
    ))
    max_Es.append(positive_angle(np.pi + max_Es[-1]))
    extremes = []
    extremes.append(ellipse_point(center_point, major_radius, minor_radius,
                                  major_axis_angle, cw_angle))
    extremes.append(ellipse_point(center_point, major_radius, minor_radius,
                                  major_axis_angle, ccw_angle))
    for E in max_Es:
        theta = positive_angle(
            math.atan2(minor_radius*math.sin(E),
                       major_radius*math.cos(E))
        )
        # Relative angle is relative to cw_angle
        relative_angle = theta - cw_angle
        if relative_angle < 0:
            relative_angle = relative_angle + 2*np.pi
        if relative_angle > 0 and relative_angle < sweep:
            extremes.append(ellipse_point(center_point, major_radius,
                                          minor_radius, major_axis_angle,
                                          theta))
    x_extremes = []
    y_extremes = []
    for ext in extremes:
        x_extremes.append(ext[0][0])
        y_extremes.append(ext[1][0])
    
    return [point_2d([min(x_extremes), min(y_extremes)]),
            point_2d([max(x_extremes), max(y_extremes)])]

def circle_arc_fit_box(
        center_point: np.ndarray, radius: float,
        point_1_angle: float, sweep_angle: float
    ) -> list[np.ndarray, np.ndarray]:
    """Returns the corners of the smallest box that the circular arc 
    would fit into. Used for sizing graphics. Uses the elliptical_arc_fit_box 
    function with its inputs set up for a circle.
    
    :param center_point: The center point of the circle
    :param radius: The major axis radius of the ellipse
    :param point_1_angle: The angle from the x-axis to the arc's first 
                          point in radians
    :param sweep_angle: The angle from the first point to the second 
                        point in radians
    :returns: A list of the minimum corner and the maximum corner 
              points of the smallest box that would fit the circle
    """
    major_axis_angle = 0
    return elliptical_arc_fit_box(
        center_point, radius, radius,
        major_axis_angle, point_1_angle, sweep_angle
    )

def multi_fit_box(
        geometry: list[dict]
    ) -> list[list[float, float] , list[float, float]]:
    """Returns the corners of the smallest box that fits all the geometry 
    in the given list. Used for sizing graphics. Does not return numpy 
    arrays, unlike the rest of trigonometry since this is intended to 
    be used outside of this module.
    
    :param geometry: A list of geometry dictionaries
    :returns: A list of the minimum corner and the maximum corner 
              points of the smallest box that would fit all the shapes.
              [[min x, min y], [max x, max y]].
    """
    x_values, y_values = [], []
    for g in geometry:
        match g["geometry_type"]:
            case "line":
                points = line_fit_box(
                    point_2d(g["start"]), point_2d(g["end"])
                )
            case "circular_arc":
                if "large_arc_flag" in g:
                    # svg-type arc definition
                    arc_definition = circle_arc_endpoint_to_center(
                        point_2d(g["start"]), point_2d(g["end"]),
                        g["large_arc_flag"], g["sweep_flag"],
                        g["radius"]
                    )
                    points = circle_arc_fit_box(
                        arc_definition[0], g["radius"],
                        arc_definition[1], arc_definition[2],
                    )
                else:
                    raise ValueError("Arc definition type not supported")
            case "elliptical_arc":
                if "large_arc_flag" in g:
                    arc_definition = elliptical_arc_endpoint_to_center(
                        point_2d(g["start"]), point_2d(g["end"]),
                        g["large_arc_flag"], g["sweep_flag"],
                        g["x_radius"], g["y_radius"],
                        g["x_axis_rotation"]
                    )
                    points = elliptical_arc_fit_box(
                        arc_definition[0],
                        g["x_radius"], g["y_radius"],
                        g["x_axis_rotation"],
                        arc_definition[1], arc_definition[2],
                    )
                else:
                    raise ValueError("Arc definition type not supported")
            case "circle":
                points = circle_fit_box(
                    point_2d(g["center"]), g["radius"]
                )
            case "ellipse":
                raise ValueError("Ellipses are not yet supported")
        min_point = pt2list(points[0])
        max_point = pt2list(points[1])
        x_values.extend([min_point[0], max_point[0]])
        y_values.extend([min_point[1], max_point[1]])
    return [[min(x_values), min(y_values)],
            [max(x_values), max(y_values)]]

