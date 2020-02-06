from pathlib import Path


class Pair:
    def __init__(self, line):
        self.id = line.pop(0)
        self.player1 = " ".join(line[:2])
        line = line[2:]
        self.player2 = " ".join(line[:2])


class Event:
    def __init__(self, lines):
        self.event_name = None
        self.session = None
        self.section = None
        self.date = None
        self.club_number = None
        self.timestamp = None
        self.director = None
        self.rating = None
        self.movement = None

        self.average = None
        self.top_score = None
        self.mp_limits = None
        self.club = None

        self.pairs = []

        self._parse_lines(lines)

    def _parse_lines(self, lines):
        def pull_value(string):
            return string[string.find(">") + 1:].strip()

        def pop_line(lines):
            return " ".join(lines.pop(0))

        event_line = " ".join(lines.pop(0))
        (event, session, section) = event_line.split("|")
        self.event_name = pull_value(event)
        self.session = pull_value(session)
        self.section = pull_value(section)

        # Dashes line
        lines.pop(0)

        date_line = pop_line(lines)
        (date, club_no, timestamp) = date_line.split("|")
        self.date = pull_value(date)
        self.club_number = pull_value(club_no)
        self.timestamp = pull_value(timestamp)

        # Dashes line
        lines.pop(0)

        director_line = pop_line(lines)
        (director, rating, movement) = director_line.split("|")
        self.director = pull_value(director)
        self.rating = pull_value(rating)
        self.movement = pull_value(movement)

        # Dashes line
        lines.pop(0)

        average_line = pop_line(lines)
        (average, top, mp_limits, club) = average_line.split("|")
        self.average = pull_value(average)
        self.top_score = pull_value(top)
        self.mp_limits = pull_value(mp_limits)
        self.club = pull_value(club)

        for i in range(5):
            lines.pop(0)

        self.pairs = [Pair(line) for line in lines[:-1]]


def find_row(rows, text):
    for i, row in enumerate(rows):
        if len(row) > 0 and row[0].startswith(text):
            return i
    return -1


def parse_events(fname: Path):
    lines = [l for l in fname.read_text().splitlines() if len(l) > 0]

    clean_lines = [[v for v in row.split() if len(v) > 0] for row in lines]

    events = []
    for i, line in enumerate(clean_lines):
        if len(line) == 0:
            continue
        elif line[0].startswith("EVENT>"):
            event_end = find_row(clean_lines[i:], "Totals") + i
            events.append(Event(clean_lines[i:event_end]))

    return events
