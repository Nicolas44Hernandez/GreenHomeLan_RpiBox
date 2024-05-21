"""Box status decorator management package"""
import logging
from functools import wraps
from server.orchestrator.box_status import orchestrator_box_status_service
from flask import jsonify

logger = logging.getLogger(__name__)

def box_sleeping(f):
    @wraps(f)
    def _verify(*args, **kwargs):

        sleeping_msg = {'message': 'Box is in deep sleep mode'}

        # Check if box is in deep sleep mode
        if orchestrator_box_status_service.is_sleeping():
            return jsonify(sleeping_msg), 412
        return f(*args, **kwargs)

    return _verify
