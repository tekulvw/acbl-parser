from pathlib import Path
from collections import Counter
from typing import List
import sqlite3

import click

from acbl_parser import parser

create_table = r"""
    CREATE TABLE IF NOT EXISTS Player(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
    );
    
    CREATE TABLE IF NOT EXISTS PlayerDate(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    date TEXT,
    session TEXT,
    play_count INTEGER,
    
    FOREIGN KEY(player_id) REFERENCES Player(id)
    );
    
    CREATE UNIQUE INDEX IF NOT EXISTS PlayerDateIndex ON "PlayerDate"("id", "player_id", "date", "session");
    """


def get_player_db_rows(events: List[parser.Event]):
    rows = []
    for event in events:
        player_counter = Counter()
        players = [player for event in events for pair in event.pairs
                   for player in (pair.player1, pair.player2)]
        player_counter.update(players)
        for player, count in player_counter.items():
            session = event.session.split(' ')[1] if ' ' in event.session else event.session
            if session == "Mor":
                session = "Morn"
            rows.append((event.timestamp, player, count, session))
    return rows


def filter_glob(filenames: List[Path], filter: int):
    filter_len = len(str(filter))
    ret = []
    for filename in filenames:
        partial_filename = filename.stem[:filter_len]
        if filter is None:
            ret.append(filename)
        elif partial_filename.isdigit() and int(partial_filename) >= filter:
            ret.append(filename)
    return ret


@click.command()
@click.option('--db-path', '-d', required=True, type=click.Path(resolve_path=True))
@click.option('--game-files', '-g', required=True, type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option('--filter', type=int, help="Only pulls data from files including and after this date.")
def update_db(db_path, game_files, filter):
    file_path = Path(db_path)
    conn = sqlite3.connect(file_path)

    conn.executescript(create_table)
    conn.commit()

    events = []
    for fname in filter_glob(list(Path(game_files).glob("*.TXT")), filter):
        try:
            events.extend(parser.parse_events(fname))
        except Exception as e:
            print(f"Could not parse {fname}")
            continue

    c = conn.cursor()

    for (i, row) in enumerate(get_player_db_rows(events)):
        print(i)
        id_res = c.execute("SELECT id FROM Player WHERE name=?", [row[1]]).fetchone()
        if id_res is None or len(id_res) == 0:
            c.execute("INSERT INTO Player VALUES(NULL, ?)", [row[1]])
            player_id = c.lastrowid
        else:
            player_id = id_res[0]

        player_date_id_res = c.execute(
            "SELECT id, play_count FROM PlayerDate WHERE player_id=? AND date=?",
            (player_id, row[0])
        ).fetchone()
        if player_date_id_res is None or len(player_date_id_res) == 0:
            c.execute(
                "INSERT INTO PlayerDate VALUES(NULL, ?, ?, ?, ?)",
                (player_id, row[0], row[3], row[2]),
            )
        else:
            curr_count = c.execute(
                "SELECT play_count FROM PlayerDate WHERE id=?",
                (player_date_id_res[0],),
            ).fetchone()
            c.execute(
                "UPDATE PlayerDate SET play_count = ? WHERE id=?",
                (curr_count[0] + row[2], player_date_id_res[0],),
            )
    conn.commit()
    c.close()
    conn.close()


if __name__ == '__main__':
    # game_filenames = (Path.cwd() / "game_files").glob("*.TXT")
    # player_counter = Counter()
    #
    # events = []
    # for fname in game_filenames:
    #     try:
    #         events.extend(parser.parse_events(fname))
    #     except Exception as e:
    #         print(f"I f'd up on: {fname}")
    #         continue
    #
    # for row in get_player_db_rows(events):
    #     print(row)
    update_db()
