#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import os
import sqlite3

from datetime import datetime, timedelta

import logging

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
logging.basicConfig(level=LOG_LEVEL)

LOGGER = logging.getLogger(__name__)

LOGGER.info('Log Level: %s', LOG_LEVEL)

HOME_DIR = (
    os.environ.get('HOME')
    or os.path.join('/home/', os.environ['USERNAME'])
)

DEFAULT_DIR = '.todo'
DEFAULT_FILE = 'todo.db'

LOCATION_DIR = os.path.join(HOME_DIR, DEFAULT_DIR)
PATH = os.path.join(LOCATION_DIR, DEFAULT_FILE)

LOGGER.info('Location: %s', LOCATION_DIR)
LOGGER.info('File name: %s', DEFAULT_FILE)
LOGGER.info('Path: %s', PATH)

os.makedirs(LOCATION_DIR, exist_ok=True)
LOGGER.info('Location is ready!')

CREATE_ITEMS = """CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    text TEXT,
    archived_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);"""

DROP_ITEMS = """DROP TABLE items;"""

SELECT_1_ITEMS = """SELECT 1 FROM items WHERE id = ? AND archived_at IS NULL LIMIT 1;"""

SELECT_ITEM = """SELECT * FROM items WHERE id = ? AND archived_at IS NULL LIMIT 1;"""

SELECT_ITEMS = """SELECT * FROM items WHERE archived_at IS NULL;"""

INSERT_ITEM = """INSERT OR IGNORE INTO items (text) VALUES (?);"""

ARCHIVE_ITEM = """UPDATE items
SET archived_at=CURRENT_TIMESTAMP
WHERE id = ?;
"""

# TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# EXPIRE_PERIOD = timedelta(days=7)

class Items:
    def __init__(self, fname=PATH):
        self.conn = sqlite3.connect(fname)
        self.conn.execute(CREATE_ITEMS)
        self.conn.commit()

    def __del__(self):
        if hasattr(self,'conn'):
            self.close()

    def insert(self, text):
        self.conn.execute(INSERT_ITEM, (text,))
        self.conn.commit()

    def query_all_items(self):
        return self.conn.execute(SELECT_ITEMS).fetchall()

    def query_item(self, item_id):
        return self.conn.execute(SELECT_ITEMS, (item_id,)).fetchone()

    def archive_item(self, item_id):
        self.conn.execute(ARCHIVE_ITEM, (item_id,))
        self.conn.commit()

    def clear(self):
        self.conn.execute(DROP_ITEMS)
        self.conn.execute(CREATE_ITEMS)
        self.conn.commit()

    def close(self):
        self.conn.close()

class Printer:
    def __init__(self, columns):
        self.columns = columns

    def print(self, items):

        width = self._calculate_width(items)

        self.print_row(self.columns, width)
        self.print_row(('-',)*len(self.columns), width)

        # Print Items
        if items:
            for item in items:
                self.print_row(item, width)
        else:
            print('<EMPTY>')

        self.print_row(('-',)*len(self.columns), width)

    def print_row(self, row, width):
            for i, value in enumerate(row[:len(self.columns)-1]):
                print(
                    self.column_item(value, width[self.columns[i]]),
                    sep='',
                    end=''
                )
            # Print Last
            print(
                self.column_item(
                    row[len(self.columns)-1],
                    width[self.columns[len(self.columns)-1]]
                )
            )

    def column_item(self, string, column_width, right_margin=2, last=False):
        string = str(string)
        if last:
            spaces = 0
        else:
            spaces = column_width - len(string)
        return string + ' '*(spaces+right_margin)

    def _calculate_width(self, items):
        if not items:
            items = [self.columns]
        max_len = {}
        for i, column in enumerate(self.columns):
            max_len[column] = max(len(str(x[i])) for x in items)
        LOGGER.info('max_len: %s', max_len)

        width = {}
        for i, column in enumerate(self.columns):
            width[column] = max(max_len[column], len(self.columns[i]))

        return width

class Todo:
    def __init__(self):
        self.items = Items()
        self.printer = Printer(columns=['id', 'text'])

    def list_items(self, _=None):
        all_items = self.items.query_all_items()
        self.printer.print(all_items)

    def add_item(self, args):
        self.items.insert(args.text)
        LOGGER.info('Inserted: %s', args.text)
        self.list_items()

    def archive_item(self, args):
        self.items.archive_item(args.id)
        LOGGER.info('Archived: %s', args.id)
        self.list_items()

def main():
    '''Main description'''
    todo = Todo()

    parser = argparse.ArgumentParser(
        description='Todo list',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.set_defaults(func=todo.list_items)


    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help')

    list_command = subparsers.add_parser('list')
    list_command.set_defaults(func=todo.list_items)

    add_command = subparsers.add_parser('add')
    add_command.add_argument('text', type=str, help='Tarefa')
    add_command.set_defaults(func=todo.add_item)

    archive_command = subparsers.add_parser('archive')
    archive_command.add_argument('id', type=int, help='Id do item')
    archive_command.set_defaults(func=todo.archive_item)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
