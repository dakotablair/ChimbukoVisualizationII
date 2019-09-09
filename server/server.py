from flask import Blueprint, jsonify, render_template, Response, json
# render_template, json, request, current_app

from . import stats as req_stats

main = Blueprint('main', __name__)


@main.before_app_first_request
def before_first_request():
    # for future usages
    pass


@main.before_app_request
def before_request():
    """Update requests per second stats."""
    req_stats.add_request()

# @main.route('/test_stream')
# def test_stream():
#     def _stream():
#         pass
#         # pubsub = red.pubsub()
#         # pubsub.subscribe('anomalystat')
#         # for message in pubsub.listen():
#         #     yield 'data: %s\n\n' % message['data']
#
#     return Response(
#         _stream(),
#         mimetype='text/event-stream',
#         headers={
#             'Cache-Control': 'no-cache',
#             'Connection': 'keep-alive'
#         }
#     )

# @main.route('/stream')
# def stream():
#     def stream_event():
#         pass
#         # pubsub = red.pubsub()
#         # pubsub.subscribe('anomalystat')
#         # # todo: handle client disconnection
#         # for msg in pubsub.listen():
#         #     print(msg)
#
#         # import time
#         # import random
#         # try:
#         #     n_ranks = 2000
#         #     while True:
#         #         stats = []
#         #         for rank in range(n_ranks):
#         #             stat = {
#         #                 'app': 0,
#         #                 'rank': rank,
#         #                 'min': random.randint(0, 20),
#         #                 'max': random.randint(10, 50),
#         #                 'mean': random.randint(0, 30)
#         #             }
#         #             stats.append(stat)
#         #         evt_type = "event: {:s}\n".format("anomalyStatUpdate")
#         #         evt_data = "data:%s\n\n" % json.dumps(stats)
#         #         packet = "{:s}{:s}".format(evt_type, evt_data)
#         #         yield packet
#         #         time.sleep(10)
#         # except GeneratorExit:
#         #     pass
#
#     return Response(
#         stream_event(),
#         mimetype='text/event-stream',
#         headers={
#             'Cache-Control': 'no-cache',
#             'Connection': 'keep-alive'
#         }
#     )

# @main.route('/test')
# def test_index():
#     return """
# <!DOCTYPE html>
# <html>
# <head>
#     <script src="//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
#     <script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/2.2.0/socket.io.slim.js"></script>
# </head>
# <body>
# <h1>Getting server updates</h1>
# SocketIO Status: <div id="status"></div>
# <div id="result"></div>
# <script>
#     $(document).ready(function(){
#         console.log('document ready');
#         var userId;
#         var namespace = '/events';
#         var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
#
#         socket.on('connect', function(){
#             console.log('socket.on.connect');
#             socket.emit('status', {status: 'I am connected!'});
#         });
#
#         socket.on('userid', function(msg){
#             console.log('socket.on.userid');
#             userId = msg.userid;
#         });
#
#         socket.on('status', function(msg){
#             console.log('socket.on.status');
#             $('#status').text(msg.status);
#         });
#
#         socket.on('updated_data', function(msg){
#             console.log(msg)
#         });
#     });
#
# //if (typeof(EventSource) !== "undefined") {
# //    var source = new EventSource('/stream');
# //    source.onmessage = function(event) {
# //        var data = JSON.parse(event.data)
# //        document.getElementById("result").innerHTML += data.message + "<br>";
# //    };
# //}
# //else {
# //    document.getElementById("result").innerHTML = "Sorry, your browser does not support SSE.";
# //}
#
# </script>
# </body>
# </html>
#     """

@main.route('/')
def index():
    """Serve client-side application"""
    return render_template('index.html')
    # return "Hello World"


@main.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({'requests_per_second': req_stats.requests_per_second()})
