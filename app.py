import os
from flask import Flask, render_template, request, json

from runstats import Statistics
from collections import defaultdict
import threading

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# app.config['SECRET_KEY'] = '51f52814-0071-11e6-a2477-000ec6c2372c'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
#     'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'db.sqlite'))
# app.config['SQLALCHMY_TRACK_MODIFICATIONS'] = False


# run stats per rank
stats = defaultdict(lambda : Statistics())
lock = threading.Lock()
def update_stats(rank, data):
    with lock:
        for num in data:
            stats[rank].push(num)

def print_stats(rank):
    with lock:
        print("Rank {} - mean: {}, std: {}".format(rank, stats[rank].mean(), stats[rank].stddev()))
# end of run stats

@app.route('/api/messages', methods=['POST'])
def new_message():
    """Post a new message"""
    if request.headers['Content-Type'] == 'application/json':
        msg = request.get_json()

        # process message (running statistics)
        rank = int(msg['rank'])
        update_stats(rank, msg['data'])
        #print_stats(rank)
        # end of process

        return "OK"
    else:
        return "415 Unsupported Media Type"


@app.route('/')
def index():
    """Serve client-side application"""
    #return render_template('index.html')
    return "Hello World"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)