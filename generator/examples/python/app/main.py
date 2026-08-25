# unit: app (app)
# capabilities: run
# effects: store, net
# uses: users, tasks, notifier
# GENERATED SKELETON — edges are declared in the project spec.

from domains.users import *  # noqa: F401,F403
from domains.tasks import *  # noqa: F401,F403
from domains.notifier import *  # noqa: F401,F403

def run():
    raise NotImplementedError


if __name__ == "__main__":
    pass  # composition root
