from proper_cli import Cli

from db import alembic


class Manage(Cli):
    db = alembic.get_proper_cli()


cli = Manage()

if __name__ == '__main__':
    cli()
