from lib.database import create_tables, connect

create_tables(connect(), delete=False)