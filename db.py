# Script that maps our database objects into easily usable classes in Python
from peewee import *

database = MySQLDatabase('YOUR DB NAME HERE', **{'host': 'YOUR DB URL HERE', 'password': 'YOUR DB PASSWORD HERE', 'port': 3306, 'user': 'YOUR DB USERNAME HERE'})

# Ignore this
class UnknownField(object):
    pass

# Ignore this
class BaseModel(Model):
    class Meta:
        database = database

# This is our User object with all the attributes it saves
class User(BaseModel):
    user_id = PrimaryKeyField(db_column='user_id')
    messenger_id = CharField(db_column='messenger_id', null=True)
    state = CharField(db_column='state', null=True)
    start_lat = FloatField(db_column='start_lat', null=True)
    start_lng = FloatField(db_column='start_lng', null=True)

    class Meta:
        db_table = 'User'
