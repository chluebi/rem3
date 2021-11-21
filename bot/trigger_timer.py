
import lib.database as db
from lib.time_handle import seconds_to_datetime
from lib.common import parse_config, get_message_link

import time
import asyncio

config = parse_config('discord')
interval = config['interval']

async def main_loop(client, db_connection):
	while True:
		old_time = time.time()
		rows = db.get_timers_threshold(db_connection, old_time + interval)

		for row in rows:
			delay = row[3] - time.time()
			client.loop.create_task(trigger_timer(delay, client, db_connection, *row))
			rows.remove(row)

		await asyncio.sleep(interval)


async def trigger_timer(delay, client, db_connection, id, label, timestamp_created, timestamp_triggered, \
 author_id, receiver_id, guild, channel, message):
	await asyncio.sleep(delay)

	if timestamp_triggered > time.time():
		return False, 0

	if timestamp_triggered < time.time() - 2*interval:
		db.delete_timer(db_connection, id)
		return True, id

	receiver = client.get_user(receiver_id)
	created_message_link = get_message_link(guild, channel, message, receiver_id)

	created_time_string = seconds_to_datetime(timestamp_created).ctime()
	triggered_time_string = seconds_to_datetime(timestamp_created).ctime()
	error_margin = str(int((time.time() - timestamp_triggered)*1000))
	m = f'''⏰ Timer: ``{label}``
	This timer was set on ``{created_time_string}``.
	This timer should've triggered on ``{triggered_time_string}``. (Error Margin: {error_margin} ms)
	Here is the message where it has been set: {created_message_link}'''

	db.delete_timer(db_connection, id)
	await receiver.send(m)
	return True, id