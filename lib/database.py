import psycopg2
from lib.common import parse_config

# standard database connection used by both services
def connect():
    config = parse_config('database')
    conn = psycopg2.connect(host=config['host'],
                            port=config['port'],
                            database=config['database'],
                            user=config['user'],
                            password=config['password'] if 'password' in config else None)
    return conn


# This function should only be called when going into a new environment
def create_tables(conn, delete=True):
    commands = []
    if delete:
        commands += [
        '''
        DROP TABLE users CASCADE;
        ''',
        '''
        DROP TABLE timers; 
        ''']
        
    commands += [
        # we actually store discord users only by id
        # discord ids are big
        '''
        CREATE TABLE users ( 
            id bigint PRIMARY KEY, 
            timezone VARCHAR(255)
        );
        ''',
        '''
        CREATE TABLE timers (
            id SERIAL,
            label text,
            timestamp_created double precision,
            timestamp_triggered double precision,
            author_id bigint REFERENCES users(id),
            receiver_id bigint REFERENCES users(id) ON DELETE CASCADE,
            guild bigint,
            channel bigint,
            message bigint,
            PRIMARY KEY (id, author_id)
        );
        ''']

    cur = conn.cursor()

    for c in commands:
        cur.execute(c)

    conn.commit()
    cur.close()


def get_user(conn, user_id):
    cur = conn.cursor()
    command = '''SELECT * FROM users WHERE id = %s'''
    cur.execute(command, (user_id,))
    row = cur.fetchone()
    cur.close()
    return row


def create_user(conn, user_id, user_timezone):
    cur = conn.cursor()
    command = '''INSERT INTO users(id, timezone) VALUES (%s, %s);'''
    cur.execute(command, (user_id, user_timezone))
    conn.commit()
    cur.close()


# This function changes the user timezone to *any* string it gets.
# So validation has to happen BEFOREHAND
def change_timezone(conn, user_id, timezone):
    cur = conn.cursor()
    command = '''UPDATE users
                SET timezone = %s
                WHERE id = %s;'''
    cur.execute(command, (timezone, user_id))
    conn.commit()
    cur.close()


def get_timers(conn, user_id, all=False):
    cur = conn.cursor()
    if all: # debug and bot usage
        command = '''SELECT * from timers'''
        cur.execute(command)
    else:
        command = '''SELECT * FROM timers WHERE receiver_id = %s'''
        cur.execute(command, (user_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_timers_threshold(conn, threshold):
    cur = conn.cursor()
    command = '''SELECT * FROM timers WHERE timestamp_triggered < %s'''
    cur.execute(command, (threshold,))
    rows = cur.fetchall()
    cur.close()
    return rows

# created_time and target_time have to be already entered in seconds away from the epoch
# created_time is entered instead of computed to not have inaccuracies caused by latency
def create_timer(conn, label, timestamp_created, timestamp_triggered, author_id, receiver_id=0, guild_id=0, channel_id=0, message_id=0):
    if receiver_id == 0:
        receiver_id = author_id
    cur = conn.cursor()
    command = '''INSERT INTO timers(label,
    timestamp_created,
    timestamp_triggered,
    author_id,
    receiver_id,
    guild,
    channel,
    message) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'''

    cur.execute(command,
    (label,
    timestamp_created,
    timestamp_triggered,
    author_id,
    receiver_id,
    guild_id,
    channel_id,
    message_id))

    conn.commit()
    cur.close()


def delete_timer(conn, id):
    cur = conn.cursor()
    command = '''DELETE FROM timers WHERE id = %s'''
    cur.execute(command, (id,))
    cur.close()