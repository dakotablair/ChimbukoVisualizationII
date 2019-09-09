from flask import request, jsonify, abort

from .. import db
from ..models import ApplicationInfo
from . import api
from ..tasks import make_async
from ..utils import timestamp

@api.route('/appinfo', methods=['POST'])
def new_appinfo():
    pass