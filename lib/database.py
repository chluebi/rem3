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

conn = connect()

class User:

    def create_table():
        command = '''
            CREATE TABLE users ( 
            id bigint PRIMARY KEY, 
            timezone VARCHAR(255)
        );'''

        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def delete_table():
        command = '''
        DROP TABLE users CASCADE;
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def __init__(self, id, timezone):
        self.id = id
        self.timezone = timezone

    def create_from_row(row):
        if row is None:
            return None
        id, timezone = row
        return User(id, timezone)

    def create(self):
        cur = conn.cursor()
        command = '''INSERT INTO users(id, timezone) VALUES (%s, %s);'''
        cur.execute(command, (self.id, self.timezone))
        conn.commit()
        cur.close()

    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return User.create_from_row(row)

    # This function changes the user timezone to *any* string it gets.
    # So validation has to happen BEFOREHAND
    def change_timezone(self, timezone):
        self.timezone = timezone
        cur = conn.cursor()
        command = '''UPDATE users
                    SET timezone = %s
                    WHERE id = %s;'''
        cur.execute(command, (self.timezone, self.id))
        conn.commit()
        cur.close()

    def get_timers(self):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE receiver_id = %s'''
        cur.execute(command, (self.id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

class Timer:

    def create_table():
        command = '''
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
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def delete_table():
        command = '''
            DROP TABLE timers;
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def __init__(self, id, label, timestamp_created, timestamp_triggered, author_id, receiver_id, guild_id, channel_id, message_id):
        self.id = id
        self.label = label
        self.timestamp_created = timestamp_created
        self.timestamp_triggered = timestamp_triggered
        self.author_id = author_id
        self.receiver_id = receiver_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id

    def create_from_row(row):
        if row is None:
            return None
        id, label, timestamp_created, timestamp_triggered, author_id, receiver_id, guild, channel, message = row
        if receiver_id == 0:
            receiver_id = author_id
        return Timer(id, label, timestamp_created, timestamp_triggered, author_id, receiver_id, guild, channel, message)

    def get_all_later_then(timestamp):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE timestamp_triggered < %s'''
        cur.execute(command, (timestamp,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

    # created_time and target_time have to be already entered in seconds away from the epoch
    # created_time is entered instead of computed to not have inaccuracies caused by latency
    def create(self):
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
        (self.label,
        self.timestamp_created,
        self.timestamp_triggered,
        self.author_id,
        self.receiver_id,
        self.guild_id,
        self.channel_id,
        self.message_id))

        conn.commit()
        cur.close()

    def delete(self):
        cur = conn.cursor()
        command = '''DELETE FROM timers WHERE id = %s'''
        cur.execute(command, (self.id,))
        cur.close()