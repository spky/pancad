"""A module providing a mapping system between pancad and cad application ids. 
The ids may be defined by pancad or read from the application, but must be 
static between runs and unique.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING
from textwrap import indent

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Hashable

class OneToOne(Mapping):
    """Represents a static, labeled relationship between two objects consisting 
    of only one source and one target.
    
    :param source: The id of the owner of the relationship.
    :param target: The id of the target of the relationship.
    :param marker: The type of relationship.
    """
    def __init__(self,
                 source: Hashable,
                 target: Hashable,
                 marker: Hashable) -> None:
        self._source = source
        self._target = target
        self._marker = marker
        self._map = {source: target, target: source}
    
    @property
    def source(self) -> Hashable:
        """The id of the owner of the relationship."""
        return self._source
    
    @property
    def target(self) -> Hashable:
        """The id of the target of the relationship."""
        return self._target
    
    @property
    def marker(self) -> Hashable:
        """The marker for the type of relationship."""
        return self._marker
    
    def __eq__(self, other):
        # Implementation copied from 6d45cd8 of 
        # cpython/Lib/_collections_abc.py::Mapping, but added marker comparison.
        if not isinstance(other, OneToOne):
            return NotImplemented
        return (dict(self.items()) == dict(other.items())
                and self.marker == other.marker)
    
    def __getitem__(self, key: Hashable) -> Hashable:
        """Returns the opposite side of the relationship."""
        return self._map[key]
    
    def __hash__(self):
        return hash((self.source, self.target, self.marker))
    
    def __iter__(self):
        return iter(self._map)
    
    def __len__(self):
        """Returns the number of relations represented by the relation. Will 
        always be one for OneToOne.
        """
        return 1
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"{{{self.source}-{self.marker}->{self.target}}}"

class OneToMany(Mapping):
    """A static map mapping a single object to either many objects or a single 
    object other multiple ways. If there is only one target and one source but 
    multiple markers, the relationship defaults to source centered.
    
    :param relations: Relations from a single object to multiple objects.
    :param marker: The type of relationship. Defaults to None for cases where
        the grouping of the relation markers is enough to differentiate the 
        relationship type.
    """
    def __init__(self,
                 relations: Sequence[OneToOne],
                 marker: Hashable):
        self._source = {relation.source for relation in relations}
        self._target = {relation.target for relation in relations}
        self._marker = marker
        self._source_centered = len(self.source) == 1
        self._relations = frozenset(relations)
        
        self._validate_inputs(self._relations)
        
        if self._source_centered:
            self._center =  tuple(self.source)[0]
        else:
            self._center =  tuple(self.target)[0]
        
        self._set_duplicate_marker_map()
        self._iter_map = {k: v for k, v in self._map.items()
                          if isinstance(k, tuple)}
    
    # Properties #
    @property
    def center(self) -> Hashable:
        """The id that all relationships in this OneToMany are attached to."""
        return self._center
    
    @property
    def source(self) -> tuple(Hashable):
        """The ids of the sources of the relationship."""
        return tuple(sorted(self._source))
    
    @property
    def source_centered(self) -> bool:
        """Indicates the OneToMany's relationships are all attached to the
        source if True and to the target if False.
        """
        return self._source_centered
    
    @property
    def target(self) -> tuple(Hashable):
        """The ids of the targets of the relationship."""
        return tuple(sorted(self._target))
    
    @property
    def marker(self) -> Hashable:
        return self._marker
    
    # Private Methods #
    def _set_duplicate_marker_map(self) -> None:
        """Initializes the map assuming there are potentially duplicate markers
        """
        self._map = defaultdict(set)
        
        # Set Many Side
        for relation in self._relations:
            if self.source_centered:
                many_end = relation.target
            else:
                many_end = relation.source
            self._map[(self.center, relation.marker)].add(many_end)
            self._map[many_end].add(self.center)
        
        # Set Center Side
        if self.source_centered:
            self._map[self.center] = self.target
        else:
            self._map[self.center] = self.source
    
    def _validate_inputs(self, relations: Sequence[OneToOne]):
        """Raises errors if the input combination is invalid.
        
        :raises ValueError: Raised if there are multiple centers, only one 
            relationship, or inconsistent relationship directions.
        """
        if not self.source_centered and len(self.target) != 1:
            relations = "\n".join([str(r) for r in self._relations])
            raise ValueError("OneToMany relations must all meet at one object."
                             f"\nRelations:\n{relations}")
        elif len(relations) == 1:
            raise ValueError("OneToMany relations need more than one relation")
        elif not self._source.isdisjoint(self._target):
            ids = self._source.intersection(self._target)
            raise ValueError(f"Inconsistent relation direction for {ids}")
    
    # Python Dunders #
    def __eq__(self, other):
        # Implementation copied from 6d45cd8 of 
        # cpython/Lib/_collections_abc.py::Mapping, but added marker comparison.
        if not isinstance(other, OneToMany):
            return NotImplemented
        return (dict(self.items()) == dict(other.items())
                and self.marker == other.marker)
    
    def __getitem__(self,
                    key: Hashable | tuple[Hashable, Hashable]
                    ) -> tuple(Hashable):
        """Returns the opposite side of the relationship when given a key that is 
        in the relationship. If given the center and a marker, it will return 
        just the keys related to the center by relations with that marker. 
        OneToMany stores the keys internally as a set, but provides them as a 
        tuple for easier access outside of the relationship.
        """
        return tuple(sorted(self._map[key]))
    
    def __iter__(self):
        return iter(self._iter_map)
    
    def __len__(self):
        """Returns the number of relations represented by the relation."""
        return len(self._relations)
    
    def __hash__(self):
        return hash((self._relations, self.marker))
    
    def __repr__(self):
        n_relations = len(self)
        return f"{{{self.center}-{self.marker}->{len(self)}Rs}}"
    
    def __str__(self):
        strings = []
        strings.append(self.__repr__())
        for relation in self._relations:
            strings.append(indent(str(relation), prefix="  "))
        return "\n".join(strings)

class ManyToMany(Mapping):
    
    def __init__(self,
                 relations: Sequence[OneToOne | OneToMany],
                 marker: Hashable,
                 markers_unique: bool=True):
        self._markers_unique = markers_unique
        self._marker = marker
        self._ends = set()
        self._relations = frozenset(relations)
        if self.markers_unique:
            self._map = {}
        else:
            self._map = defaultdict(lambda: defaultdict(set))
        
        for relation in relations:
            self.add_relation(relation)
    
    @property
    def marker(self) -> Hashable:
        return self._marker
    
    @property
    def markers_unique(self) -> bool:
        return self._markers_unique
    
    def add(self, relation: OneToOne | OneToMany):
        source_relation_key = (relation.source, relation.marker)
        target_relation_key = (relation.target, relation.marker)
        if self.markers_unique:
            if source_relation_key in self._relation_map:
                raise ValueError(
                    f"{relation.marker} relation has already been added for"
                    f" {relation.source} and {relation.target}. Use a nonunique"
                    " marker many-to-many if that is required. If replacing the"
                    " relation, delete the existing one and then add it")
            else:
                self._map.update({source_relation_key: relation,
                                  target_relation_key: relation})
                self._ends.add(relation.source)
                self._ends.add(relation.target)
        else:
            self._map[source_relation_key].add(relation)
            self._map[target_relation_key].add(relation)
        # Make new frozenset of relations to include new relationship
        self._relations = self._relations.union({relation})
    
    def __getitem__(self, key: Hashable):
        if key in self._map:
            return self._map[key]
        
        key_relations = {k: v for k, v in self._map.items() if k[0] == key}
        if key_relations:
            return key_relations
        else:
            raise KeyError(f"{key} not found!")
    
    def __iter__(self):
        pass
    
    def __len__(self):
        return len(self._relations)