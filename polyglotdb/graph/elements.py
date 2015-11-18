
from .helper import key_for_cypher, value_for_cypher

class ClauseElement(object):
    sign = ''
    template = "{} {} {}"
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return '<ClauseElement \'{}\'>'.format(self.for_cypher())

    def __hash__(self):
        return hash((self.attribute, self.sign, self.value))

    def cypher_value_string(self):
        return '{%s}' % self.attribute.alias

    @property
    def annotations(self):
        annotations = [self.attribute.base_annotation]
        try:
            annotations.append(self.value.base_annotation)
        except AttributeError:
            pass
        return annotations

    @property
    def attributes(self):
        attributes = [self.attribute]
        if hasattr(self.value, 'annotation'):
            attributes.append(self.value)
        return attributes

    def for_cypher(self):
        try:
            value = self.value.for_cypher()
        except AttributeError:
            value = self.cypher_value_string()
        return self.template.format(self.attribute.for_cypher(),
                                self.sign,
                                value)

class EqualClauseElement(ClauseElement):
    sign = '='

class GtClauseElement(ClauseElement):
    sign = '>'

class GteClauseElement(ClauseElement):
    sign = '>='

class LtClauseElement(ClauseElement):
    sign = '<'

class LteClauseElement(ClauseElement):
    sign = '<='

class NotEqualClauseElement(ClauseElement):
    sign = '<>'

class InClauseElement(ClauseElement):
    sign = 'IN'

class RegexClauseElement(ClauseElement):
    sign = '=~'

class ContainsClauseElement(ClauseElement):
    sign = 'contains'
    template = '''({alias})<-[:contained_by]-({token})-[:is_a]->({type} {{{label}: {value}}})'''
    def for_cypher(self):
        kwargs = {'alias':self.attribute.annotation.alias,
                'value':value_for_cypher(self.value),
                'label': key_for_cypher(self.attribute.label),
                'type': ':{}_type'.format(self.attribute.annotation.type),
                'token': ':{}'.format(self.attribute.annotation.type)}
        return self.template.format(**kwargs)

class AlignmentClauseElement(ClauseElement):
    template = "{first}.label = {second}.label"
    side = ''
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __hash__(self):
        return hash((self.first, self.template, self.second))

    @property
    def annotations(self):
        return [self.first, self.second]

    @property
    def attributes(self):
        return [self.first.id]

    def for_cypher(self):
        kwargs = {'second_node_alias': self.second.alias,
                'first_node_alias': self.first.alias}
        return self.template.format(**kwargs)

class RightAlignedClauseElement(AlignmentClauseElement):
    template = '''not ({first_node_alias})-[:precedes]->()-[:contained_by*]->({second_node_alias})'''
    alias_to_use = 'end_alias'

class LeftAlignedClauseElement(AlignmentClauseElement):
    template = '''not ({first_node_alias})<-[:precedes]-()-[:contained_by*]->({second_node_alias})'''
    alias_to_use = 'begin_alias'

class NotRightAlignedClauseElement(RightAlignedClauseElement):
    template = '''({first_node_alias})-[:precedes]->()-[:contained_by*]->({second_node_alias})'''

class NotLeftAlignedClauseElement(LeftAlignedClauseElement):
    template = '''({first_node_alias})<-[:precedes]-()-[:contained_by*]->({second_node_alias})'''

