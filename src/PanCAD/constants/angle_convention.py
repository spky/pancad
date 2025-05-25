from enum import Flag, auto

class AngleConvention(Flag):
    
    # Unless explicitly stated, 3D angle is bounded between 0 and pi
    PLUS_PI = auto() # Angle always between 0 and pi, sign ignored
    PLUS_TAU = auto() # Angle always between 0 and 2pi. Angle in 3D still <pi
    PLUS_180 = auto() # Angle always between 0 and 180, sign ignored
    PLUS_360 = auto() # Angle always between 0 and 360. Angle in 3D still <180
    SIGN_PI = auto() # Angle always between -pi and pi. Sign ignored in 3D
    SIGN_180 = auto() # Angle always between -180 and 180. Sign ignored in 3D