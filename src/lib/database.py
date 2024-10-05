from venv import create
import psycopg2
import os
import random

# standard database connection used by both services
def connect():
    conn = psycopg2.connect(host=os.getenv('POSTGRES_HOST'),
                            port=int(os.getenv('POSTGRES_PORT')),
                            database=os.getenv('POSTGRES_DB'),
                            user=os.getenv('POSTGRES_USER'),
                            password=os.getenv('POSTGRES_PASSWORD'),
                            options='-c search_path=public')
    return conn

conn = connect()

class Guild:

    @staticmethod
    def create_table():
        command = '''
            CREATE TABLE guilds ( 
            id bigint PRIMARY KEY, 
            allow_timers boolean,
            allow_repeating boolean,
            extract_mentions boolean
        );'''

        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    @staticmethod
    def delete_table():
        command = '''
        DROP TABLE guilds CASCADE;
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def __init__(self, id, allow_timers, allow_repeating, extract_mentions):
        self.id = id
        self.allow_timers = allow_timers
        self.extract_mentions = extract_mentions
        self.allow_repeating = allow_repeating

    @staticmethod
    def create(id, allow_timers, allow_repeating, extract_mentions):
        return Guild(id, allow_timers, allow_repeating, extract_mentions)

    @staticmethod
    def create_from_row(row):
        if row is None:
            return None
        id, allow_timers, allow_repeating, extract_mentions = row
        return Guild.create(id, allow_timers, allow_repeating, extract_mentions)

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM guilds WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return Guild.create_from_row(row)

    def insert(self):
        cur = conn.cursor()
        command = '''INSERT INTO guilds(id, allow_timers, allow_repeating, extract_mentions) VALUES (%s, %s, %s, %s);'''
        cur.execute(command, (self.id, self.allow_timers, self.allow_repeating, self.extract_mentions))
        conn.commit()
        cur.close()

    def update(self):
        cur = conn.cursor()
        command = '''UPDATE guilds
                    SET allow_timers = %s,
                    allow_repeating = %s,
                    extract_mentions = %s
                    WHERE id = %s;'''
        cur.execute(command, (self.allow_timers, self.allow_repeating, self.extract_mentions, self.id))
        conn.commit()
        cur.close()

    def get_timers(self):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE receiver_guild_id = %s'''
        cur.execute(command, (self.id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

class User:

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def create(id, timezone):
        return User(id, timezone)

    @staticmethod
    def create_from_row(row):
        if row is None:
            return None
        id, timezone = row
        return User(id, timezone)

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return User.create_from_row(row)

    def insert(self):
        cur = conn.cursor()
        command = '''INSERT INTO users(id, timezone) VALUES (%s, %s);'''
        cur.execute(command, (self.id, self.timezone))
        conn.commit()
        cur.close()

    def change_timezone(self, timezone):
        self.timezone = timezone
        cur = conn.cursor()
        command = '''UPDATE users
                    SET timezone = %s
                    WHERE id = %s;'''
        cur.execute(command, (self.timezone, self.id))
        conn.commit()
        cur.close()

    def get_timers_by_receiver(self):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE receiver_id = %s'''
        cur.execute(command, (self.id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

    def get_timers_by_author(self):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE author_id = %s'''
        cur.execute(command, (self.id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

class Allow:

    @staticmethod
    def create_table():
        command = '''
            CREATE TABLE allows ( 
            sender_id bigint,
            receiver_id bigint,
            PRIMARY KEY(sender_id, receiver_id)
        );'''

        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    @staticmethod
    def delete_table():
        command = '''
        DROP TABLE allows CASCADE;
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    def __init__(self, sender_id, receiver_id):
        self.sender_id = sender_id
        self.receiver_id = receiver_id

    @staticmethod
    def create(sender_id, receiver_id):
        return Allow(sender_id, receiver_id)

    @staticmethod
    def create_from_row(row):
        if row is None:
            return None
        sender_id, receiver_id = row
        return Allow(sender_id, receiver_id)

    @staticmethod
    def get(sender_id, receiver_id):
        cur = conn.cursor()
        command = '''SELECT * FROM allows WHERE sender_id = %s AND receiver_id = %s'''
        cur.execute(command, (sender_id, receiver_id))
        row = cur.fetchone()
        cur.close()
        return Allow.create_from_row(row)

    @staticmethod
    def get_by_sender(sender_id):
        cur = conn.cursor()
        command = '''SELECT * FROM allows WHERE sender_id = %s'''
        cur.execute(command, (sender_id, ))
        rows = cur.fetchall()
        cur.close()
        return [Allow.create_from_row(row) for row in rows]

    @staticmethod
    def get_by_receiver(receiver_id):
        cur = conn.cursor()
        command = '''SELECT * FROM allows WHERE receiver_id = %s'''
        cur.execute(command, (receiver_id, ))
        rows = cur.fetchall()
        cur.close()
        return [Allow.create_from_row(row) for row in rows]

    def insert(self):
        cur = conn.cursor()
        command = '''INSERT INTO allows(sender_id, receiver_id) VALUES (%s, %s);'''
        cur.execute(command, (self.sender_id, self.receiver_id))
        conn.commit()
        cur.close()

    def delete(self):
        cur = conn.cursor()
        command = '''DELETE FROM allows WHERE sender_id = %s AND receiver_id = %s'''
        cur.execute(command, (self.sender_id, self.receiver_id))
        cur.close()



class Timer:

    @staticmethod
    def create_table():
        command = '''
        CREATE TABLE timers (
            id bigint UNIQUE,
            label text,
            created_timestamp double precision,
            triggered_timestamp double precision,
            repeat_seconds double precision,
            author_id bigint REFERENCES users(id),
            author_guild_id bigint,
            author_channel_id bigint,
            author_message_id bigint,
            receiver_id bigint,
            receiver_guild_id bigint,
            receiver_channel_id bigint,
            receiver_message_id bigint,
            PRIMARY KEY (id, author_id)
        );
        '''
        
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    @staticmethod
    def delete_table():
        command = '''
            DROP TABLE timers;
        '''
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()

        if row is None:
            return None

        return Timer.create_from_row(row)

    @staticmethod
    def get_all_author(author_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE author_id = %s'''
        cur.execute(command, (author_id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]


    @staticmethod
    def get_all_user_receiver(receiver_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE receiver_id = %s'''
        cur.execute(command, (receiver_id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]


    @staticmethod
    def get_all_guild_receiver(receiver_guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE receiver_guild_id = %s'''
        cur.execute(command, (receiver_guild_id,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

    @staticmethod
    def get_all_later_then(timestamp):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE triggered_timestamp < %s'''
        cur.execute(command, (timestamp,))
        rows = cur.fetchall()
        cur.close()
        return [Timer.create_from_row(row) for row in rows]

    @staticmethod
    def get_by_author(id, author_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE id = %s AND author_id = %s'''
        cur.execute(command, (id, author_id))
        row = cur.fetchone()
        cur.close()
        return Timer.create_from_row(row)

    @staticmethod
    def get_by_receiver(id, receiver_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE id = %s AND receiver_id = %s'''
        cur.execute(command, (id, receiver_id))
        row = cur.fetchone()
        cur.close()
        return Timer.create_from_row(row)

    @staticmethod
    def get_by_guild(id, guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM timers WHERE id = %s AND receiver_guild_id = %s'''
        cur.execute(command, (id, guild_id))
        row = cur.fetchone()
        cur.close()
        return Timer.create_from_row(row)

    def __init__(self, id, label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id):
        self.id = id
        self.label = label
        self.created_timestamp = created_timestamp
        self.triggered_timestamp = triggered_timestamp
        self.repeat_seconds = repeat_seconds
        self.author_id = author_id
        self.author_guild_id = author_guild_id
        self.author_channel_id = author_channel_id
        self.author_message_id = author_message_id
        self.receiver_id = receiver_id
        self.receiver_guild_id = receiver_guild_id
        self.receiver_channel_id = receiver_channel_id
        self.receiver_message_id = receiver_message_id

    @staticmethod
    def create(label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id):
        MIN_ID = 10**5
        MAX_ID = 10**6 - 1
        id = random.randint(MIN_ID, MAX_ID)
        while not Timer.get(id) is None:
            id = random.randint(MIN_ID, MAX_ID)

        return Timer(id, label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id)

    @staticmethod
    def create_personal_timer(label, created_timestamp, triggered_timestamp, author_id, receiver_id, author_guild_id, author_channel_id, author_message_id, repeat=-1):
        label = label
        created_timestamp = created_timestamp
        triggered_timestamp = triggered_timestamp
        repeat_seconds = repeat
        author_id = author_id
        author_guild_id = author_guild_id
        author_channel_id = author_channel_id
        author_message_id = author_message_id
        receiver_id = receiver_id
        receiver_guild_id = 0
        receiver_channel_id = 0
        receiver_message_id = 0
        return Timer.create(label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id)

    @staticmethod
    def create_guild_timer(label, created_timestamp, triggered_timestamp, author_id, author_guild_id, author_channel_id, author_message_id, receiver_guild_id, receiver_channel_id, repeat=-1):
        label = label
        created_timestamp = created_timestamp
        triggered_timestamp = triggered_timestamp
        repeat_seconds = repeat
        author_id = author_id
        author_guild_id = author_guild_id
        author_channel_id = author_channel_id
        author_message_id = author_message_id
        receiver_id = 0
        receiver_guild_id = receiver_guild_id
        receiver_channel_id = receiver_channel_id
        receiver_message_id = 0
        return Timer.create(label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id)

    @staticmethod
    def create_from_row(row):
        if row is None:
            return None
        id, label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id = row
        return Timer(id, label, created_timestamp, triggered_timestamp, repeat_seconds, author_id, author_guild_id, author_channel_id, author_message_id, receiver_id, receiver_guild_id, receiver_channel_id, receiver_message_id)


    # created_time and target_time have to be already entered in seconds away from the epoch
    # created_time is entered instead of computed to not have inaccuracies caused by latency
    def insert(self):
        cur = conn.cursor()
        command = '''INSERT INTO timers(
        id,
        label,
        created_timestamp,
        triggered_timestamp,
        repeat_seconds,
        author_id,
        author_guild_id,
        author_channel_id,
        author_message_id,
        receiver_id,
        receiver_guild_id,
        receiver_channel_id,
        receiver_message_id
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''

        cur.execute(command,
        (
        self.id,
        self.label,
        self.created_timestamp,
        self.triggered_timestamp,
        self.repeat_seconds,
        self.author_id,
        self.author_guild_id,
        self.author_channel_id,
        self.author_message_id,
        self.receiver_id,
        self.receiver_guild_id,
        self.receiver_channel_id,
        self.receiver_message_id
        ))

        conn.commit()
        cur.close()

    def delete(self):
        cur = conn.cursor()
        command = '''DELETE FROM timers WHERE id = %s'''
        cur.execute(command, (self.id,))
        cur.close()
    

for cl in [User, Timer, Allow, Guild]:
    try:
        cl.create_table()
    except:
        conn.rollback()