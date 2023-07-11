import sqlite3 as sq


def sql_start():
	global base, cur
	base = sq.connect('data.db')
	cur = base.cursor()
	cur.execute('''
		CREATE TABLE IF NOT EXISTS groups (
			id INTEGER PRIMARY KEY,
			"group" TEXT
			);
		''')
	base.commit()

async def get_group(id):
    return cur.execute('SELECT "group" FROM groups WHERE id=?', (id,)).fetchone()[0]

async def set_group_in_db(id, group):
    cur.execute('INSERT INTO groups VALUES (?, ?)', (id, group))
    base.commit()

async def change_group_in_db(id, group):
    cur.execute('UPDATE groups SET "group" = ? WHERE id = ?', (group, id))
    base.commit()

