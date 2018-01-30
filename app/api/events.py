from flask import jsonify, request, url_for
from app import db
from app.api import api
from app.models import Event


@api.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    return jsonify(Event.query.get_or_404(id).to_dict())


@api.route('/events', methods=['GET'])
def get_events():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Event.to_collection_dict(
        Event.query, page, per_page, 'api.get_events')
    return jsonify(data)


@api.route('/events', methods=['POST'])
def create_event():
    event = Event()
    data = request.get_json()
    event.from_dict(data)
    db.session.add(event)
    db.session.commit()
    response = jsonify(event.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_event', id=event.id)
    return response


@api.route('/events/<int:id>', methods=['PUT'])
def update_event(id):
    event = Event.query.get_or_404(id)
    data = request.get_json() or {}
    event.from_dict(request.get_json() or {})
    db.session.commit()
    return jsonify(event.to_dict())


@api.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({})
