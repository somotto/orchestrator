from flask import Flask, request, jsonify

from app.queue_sender import send_message_to_billing_queue
from app.proxy import bp as bp_proxy


def create_app():

    app = Flask(__name__)

    app.register_blueprint(bp_proxy)

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        response = jsonify({'error': f'{error}'})
        response.status_code = 500
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        response = jsonify({'error': 'Not Found'})
        response.status_code = 404
        return response

    return app