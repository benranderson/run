from flask import jsonify, request
from app.api import api
from app.models import Event


@api.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())


@api.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)


# @api.route('/workouts/<int:id>', methods=['GET'])
# def get_workout(id):
#     return jsonify(Workout.query.get_or_404(id).to_dict())


# @api.route('/users/<int:id>/workouts', methods=['GET'])
# def get_user_workouts(id):
#     user = User.query.get_or_404(id)
#     page = request.args.get('page', 1, type=int)
#     per_page = min(request.args.get('per_page', 10, type=int), 100)
#     data = Workout.to_collection_dict(user.plan.workouts, page, per_page,
#                                       'api.get_user_workouts', id=id)
#     return jsonify(data)


@api.route('/users', methods=['POST'])
def create_user(id):
    pass


@api.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    pass
