import re
import logging
from datetime import datetime

__logname__ = 'hyppy'


class List(object):
    def __init__(self):
        self.generated = None
        self.items = []

    @classmethod
    def parse(cls, content):
        self = cls()
        lines, comments = cls.get_lines(content)

        self.parse_comments(comments)
        self.items = cls.tokenize(lines)

        return self

    @staticmethod
    def get_lines(content):
        # Strip blank lines and comments
        lines = content.split("\n")

        # Remove comments and blank lines
        lines[:] = [l for l in lines if len(l.strip()) > 0]

        comments = [l for l in lines if l[0] == '#']
        lines[:] = [l for l in lines if l[0] != '#']

        return lines, comments

    def parse_comments(self, comments):
        for c in comments:
            # Parse generated timestamp
            m = re.match('^# Generated: (?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$', c)
            if m is not None:
                self.generated = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def tokenize(lines):
        return [line.split(' ') for line in lines]

PATTERNS = {
    'alliance_tag': '[A-Za-z0-9-_\.@=/~\*\:,]{0,5}',
    'planet_name': '[A-Za-z0-9-_\.@/]+',
    'player_name': '[A-Za-z0-9-_\./]+',
}


class PlayerList(List):
    @staticmethod
    def tokenize(lines):
        format = '^(?P<name>' + PATTERNS['player_name'] + ') ' + \
            '(?P<inf>\d+) ' + \
            '(?P<inf_sc>\d+) ' + \
            '(?P<inf_score>\d+) ' + \
            '(?P<hyp>\d+) ' + \
            '(?P<idr>\d+) ' + \
            '(?P<idr_score>\d+) ' + \
            '(?P<idr_sc>\d+) ' + \
            '(?P<supercluster>\d+) ' + \
            '(?P<location>.*)$'

        tokens = []
        for line in lines:
            match = re.match(format, line)
            if match is None:
                logging.getLogger(__logname__).warn("Unparseable player line: '%s' with pattern '%s'" % (line, format))
            else:
                tokens.append({k: v.strip() for k, v in match.groupdict().iteritems()})

        return tokens

class PlanetList(List):
    @staticmethod
    def tokenize(lines):
        format = '^(?P<id>\d+) ' + \
                 '(?P<name>' + PATTERNS['planet_name'] + ') ' + \
                 '(?P<govt>\d) ' + \
                 '(?P<x>-?\d+) ' + \
                 '(?P<y>-?\d+) ' + \
                 '(?P<race>\d) ' + \
                 '(?P<prod>\d) ' + \
                 '(?P<activity>\d+) ' + \
                 '\[(?P<pub_tag>' + PATTERNS['alliance_tag'] + ')\] ' + \
                 '(?P<civ>\d+) ' + \
                 '(?P<size>\d+)$'

        tokens = []
        for line in lines:
            match = re.match(format, line)
            if match is None:
                logging.getLogger(__logname__).warn("Unparseable planet line: '%s' with pattern '%s'" % (line, format))
            else:
                tokens.append({k: v.strip() for k, v in match.groupdict().iteritems()})

        return tokens
