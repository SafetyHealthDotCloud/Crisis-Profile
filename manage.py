import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db


app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
from flask_alchemydumps import AlchemyDumps
alchemydumps = AlchemyDumps(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)
manager.add_command('alchemydumps', AlchemyDumps)
if __name__ == '__main__':
    manager.run()
    db.create_all()