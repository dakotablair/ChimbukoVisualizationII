# needed for using redis in this configuration
from gevent import monkey
monkey.patch_all()

import sys

from server import create_app, socketio

if __name__ == "__main__":
	host=sys.argv[1]
	port=sys.argv[2]

	print("host: ", host)
	print("port: ", port)

	app = create_app()
	socketio.run(app, host=host, port=port, debug=False, use_reloader=False)

