import sys
import eventlet
eventlet.monkey_patch()

from server import create_app, socketio

if __name__ == "__main__":
	host=sys.argv[1]
	port=sys.argv[2]

	print("host: ", host)
	print("port: ", port)

	app = create_app()
	socketio.init_app(app, host=host, port=port, debug=False, use_reloader=False)
