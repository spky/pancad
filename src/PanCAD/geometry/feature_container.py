"""A module providing a class to represent the objects that contain a feature of 
CAD geometry. In most CAD applications this may be the same as the CAD file, but 
some applications have subgroups, folders, and bodies (bodies that are not a 
feature by themselves, but just contain other geometry, like Bodies and Parts in 
FreeCAD). Separating the software owner of a feature from the geometry 
dependencies and children should allow these concepts to be translated 
between applications.
"""
from __future__ import annotations

from textwrap import indent
from typing import Sequence, Self

from PanCAD.geometry import PanCADThing, AbstractFeature

class FeatureContainer(AbstractFeature):
    """A class representing a grouping of features in CAD applications. Strictly 
    defines only the software ownership, not what geometry the features modify 
    or create.
    """
    
    def __init__(self,
                 features: Sequence[AbstractFeature]=None,
                 uid: str=None,
                 name: str=None,
                 context: FeatureContainer=None,) -> None:
        self.uid = uid
        self.name = name
        self.context = context
        self._uid_to_feature = {self.uid: self}
        self.features = features
    
    # Public Methods #
    def add_feature(self, feature: AbstractFeature) -> Self:
        """Adds a feature to the FeatureContainer.
        
        :param feature: The feature to add.
        :returns: The updated FeatureContainer.
        :raises LookupError: Raised if the feature's dependencies are not 
            already in the FeatureContainer.
        """
        dependencies = feature.get_dependencies()
        if (all([d in self for d in dependencies])
                 or all([d is None for d in dependencies])):
            # Only add feature if it has no dependencies or all dependencies are 
            # available to the container already.
            self._features = self._features + (feature,)
            self._uid_to_feature[feature.uid] = feature
            if feature.context is None:
                # Feature context is set to the container if it is not already 
                # another context since it is now inside a new context.
                feature.context = self
        else:
            missed = filter(lambda d: d not in self, dependencies)
            raise LookupError(f"Dependencies for {repr(feature)} are missing"
                              f" from part: {list(missed)}")
        return self
    
    def get_dependencies(self) -> tuple[AbstractFeature]:
        if self.context is None:
            return self._features
        else:
            return self._features + (self.context,)
    
    # Getters #
    @property
    def context(self) -> FeatureContainer | None:
        return self._context
    
    @property
    def features(self) -> tuple[AbstractFeature]:
        return self._features
    
    # Setters #
    @context.setter
    def context(self, feature: FeatureContainer | None) -> None:
        if isinstance(feature, FeatureContainer) or feature is None:
            self._context = feature
        else:
            raise TypeError("FeatureContainers can only be contained by other"
                            " FeatureContainers or None, provided:"
                            f" {feature}")
    
    @features.setter
    def features(self, features: Sequence[AbstractFeature]) -> None:
        self._features = tuple()
        if features is not None:
            for feature in features:
                self.add_feature(feature)
    
    # Python Dunders #
    def __contains__(self, item: object) -> bool:
        return (isinstance(item, PanCADThing)
                and item.uid in self._uid_to_feature)
    
    def __repr__(self) -> str:
        n_features = len(self.features)
        return f"<PanCADFeatureContainer'{self.name}'({n_features}feats)>"
    
    def __str__(self) -> str:
        """Returns a summary of what is inside of the FeatureContainer."""
        INDENTATION = "    "
        summary = []
        if self.context is None:
            context_name = "None"
        else:
            context_name = self.context.name
        
        summary.append(f"FeatureContainer '{self.name}',"
                       f" Context: {context_name}")
        
        for feature in self.features:
            dependency_lines = []
            for dependency in feature.get_dependencies():
                dependency_lines.append(
                    f"{dependency.__class__.__name__} '{dependency.name}'"
                )
            dependency_iter = iter(dependency_lines)
            preface = "Dependencies: "
            dependency_summary = [preface + next(dependency_iter)]
            dep_indent = " "*len(preface)
            dependency_summary.extend(
                [indent(line, dep_indent) for line in dependency_iter]
            )
            feature_str = "\n".join(str(feature).split("\n")[1:])
            feature_summary = "\n".join(
                [f"{feature.__class__.__name__} '{feature.name}'",
                 indent("\n".join(dependency_summary), INDENTATION),
                 indent(feature_str, INDENTATION),]
            )
            summary.append(indent(feature_summary, INDENTATION))
        return "\n".join(summary)