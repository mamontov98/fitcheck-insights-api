from flask import request, jsonify, Blueprint
from mongodb_connection_holder import MongoConnectionHolder
from datetime import datetime
import uuid

feature_toggle_blueprint = Blueprint('feature_toggle', __name__)

# 1. create a new feature toggle item:
@feature_toggle_blueprint.route('/feature-toggle', methods=['POST'])
def create_feature_toggle():
    """
    Create a new feature toggle
    ---
    parameters:
        - name: feature_toggle
          in: body
          required: true
          description: The feature toggle to create
          schema:
            id: feature_toggle
            required:
                - package_name
                - name
                - description
                - beginning_date
                - expiration_date
            properties:
                package_name:
                    type: string
                    description: The name of the package
                name:
                    type: string
                    description: The name of the feature
                description:
                    type: string
                    description: The description of the feature toggle
                beginning_date:
                    type: string
                    description: The start date of the feature toggle
                expiration_date:
                    type: string
                    description: The end date of the feature toggle
    responses:
        201:
            description: The feature toggle was created successfully
        400:
            description: The request was invalid
        500:
            description: An error occurred while creating the feature toggle
    """
    data = request.json
    db = MongoConnectionHolder.get_db()

    # check connection:
    if db is None:
        return jsonify({'error': 'Could not connect to the database'}), 500

    # check data:
    if not all(key in data for key in ['package_name',  'name', 'description', 'beginning_date', 'expiration_date']):
        return jsonify({'error': 'Invalid request!'}), 400

    try:
        # parse:
        beginning_date = datetime.strptime(
            data['beginning_date'], "%Y-%m-%d %H:%M:%S"
        )
        expiration_date = datetime.strptime(
            data['expiration_date'], "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD HH:MM:SS'}), 400

    if beginning_date > expiration_date:
        return jsonify({'error': 'Beginning date must be before expiration date'}), 400

    # Create the item:
    feature_toggle_item = {
        "_id": str(uuid.uuid4()),
        "name": data['name'],
        "description": data["description"],
        "beginning_date": beginning_date,
        "expiration_date": expiration_date,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    #insert item to db:
    package_collection = db[data['package_name']]
    package_collection.insert_one(feature_toggle_item)

    return jsonify({"message": "Feature toggle created successfully", '_id': feature_toggle_item['_id']}), 201


# 2. get all features for package by name:
@feature_toggle_blueprint.route('/feature-toggles/<package_name>', methods=['GET'])
def get_all_package_feature_toggles(package_name):
    """
    Get all feature toggles for a package
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
    responses:
        200:
            description: List of all feature toggles    
    """
    all_features = []
    db = MongoConnectionHolder.get_db()
    if db is None:
        # Helpful error message for debugging
        return jsonify({'error': 'Database not initialized'}), 500

    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Find all feature toggles
    for feature in package_collection.find():
        all_features.append(feature)
    return jsonify(all_features), 200

# 3. Get a feature toggle by id for package name
@feature_toggle_blueprint.route('/feature-toggle/<package_name>/<feature_id>', methods=['GET'])
def get_feature_toggle_details(package_name, feature_id):
    """
    Get details of a specific feature toggle
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
        - name: feature_id
          in: path
          type: string
          required: true
          description: ID of the feature toggle to get
    responses:
        200:
            description: Feature toggle details
        404:
            description: Feature toggle not found
    """
    db = MongoConnectionHolder.get_db()
    if db is None:
        # Helpful error message for debugging
        return jsonify({'error': 'Database not initialized'}), 500

    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Find specific feature toggle
    for feature in package_collection.find():
        if feature['_id'] == feature_id:
            return jsonify(feature), 200

    return jsonify({'error': 'Feature toggle not found'}), 404


# 4. Get all active feature toggles for package name
@feature_toggle_blueprint.route('/feature-toggles/<package_name>/active', methods=['GET'])
def get_active_feature_toggles(package_name):
    """
    Get all active feature toggles
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
    responses:
        200:
            description: List of active feature toggles
    """
    current = datetime.now()
    db = MongoConnectionHolder.get_db()
    if db is None:
        # Helpful error message for debugging
        return jsonify({'error': 'Database not initialized'}), 500
    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Find active feature toggles
    active_features = list(package_collection.find({
        'expiration_date': {'$gt': current},
        'beginning_date': {'$lt': current}
    }))

    return jsonify(active_features), 200


# 5. Get all active feature toggles for package name and date
@feature_toggle_blueprint.route('/feature-toggles/<package_name>/by-date', methods=['GET'])
def get_feature_toggles_by_date(package_name):
    """
    Get all active feature toggles by a specific date
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
        - name: date
          in: query
          type: string
          required: true
          description: Date in the format YYYY-MM-DD
    responses:
        200:
            description: List of active feature toggles by date
    """
    date_str = request.args.get('date', "")
    db = MongoConnectionHolder.get_db()
    if db is None:
        # Helpful error message for debugging
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # Parse specific date
        specific_date = datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD'}), 400

    features_by_date = []
    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Find feature toggles by date
    active_features_by_date = list(package_collection.find({
        'expiration_date': {'$gte': specific_date},
        'beginning_date': {'$lte': specific_date}
    }))
    for feature in active_features_by_date:
        features_by_date.append(feature)
    return jsonify(features_by_date), 200


# 6. Update a feature toggle by id for package name
@feature_toggle_blueprint.route('/feature-toggle/<package_name>/<feature_id>/update-dates', methods=['PUT'])
def update_feature_toggle_dates(package_name, feature_id):
    """
    Update the beginning and expiration dates of a feature toggle
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
        - name: feature_id
          in: path
          type: string
          required: true
          description: ID of the feature toggle to update
        - name: updated_data
          in: body
          required: true
          description: The feature toggle to create
          schema:
              id: UpdatedData
              optional:
              - expiration_date
              - beginning_date
              properties:
                expiration_date:
                  type: string
                  description: Expiration date of the feature toggle in the format YYYY-MM-DD HH:MM:SS
                beginning_date:
                  type: string
                  description: Beginning date of the feature toggle in the format YYYY-MM-DD HH:MM:SS
    responses:
        200:
            description: Dates updated
        400:
            description: Invalid date format
        404:
            description: Feature toggle not found
    """
    data = request.json
    new_expiration_date = None
    new_beginning_date = None
    db = MongoConnectionHolder.get_db()
    if db is None:
        # Helpful error message for debugging
        return jsonify({'error': 'Database not initialized'}), 500

    # Check for new dates in request data
    if 'expiration_date' in data:
        new_expiration_date = data.get('expiration_date')
    if 'beginning_date' in data:
        new_beginning_date = data.get('beginning_date')

    if not 'expiration_date' in data and not 'beginning_date' in data:
        return jsonify({'error': 'No dates provided'}), 400

    try:
        # Parse new dates
        if new_expiration_date:
            new_expiration_date = datetime.strptime(
                new_expiration_date, '%Y-%m-%d %H:%M:%S')
        if new_beginning_date:
            new_beginning_date = datetime.strptime(
                new_beginning_date, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD HH:MM:SS'}), 400

    if new_beginning_date and new_expiration_date and new_beginning_date > new_expiration_date:
        return jsonify({'error': 'Beginning date must be before expiration date'}), 400

    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Find and update feature toggle
    feature = package_collection.find_one({'_id': feature_id})
    if feature:
        if new_expiration_date:
            if new_expiration_date < feature['beginning_date']:
                return jsonify({'error': 'Expiration date cannot be before beginning date'}), 400
            feature['expiration_date'] = new_expiration_date
        if new_beginning_date:
            if new_beginning_date > feature['expiration_date']:
                return jsonify({'error': 'Beginning date cannot be after expiration date'}), 400
            feature['beginning_date'] = new_beginning_date

        package_collection.update_one(
            {'_id': feature['_id']},
            {'$set': feature}
        )
        return jsonify({'message': 'Dates updated'}), 200

    return jsonify({'error': 'Feature toggle not found'}), 404


# 7. Delete all feature toggles for package name
@feature_toggle_blueprint.route('/feature-toggles/<package_name>', methods=['DELETE'])
def delete_all_feature_toggles(package_name):
    """
    Delete all feature toggles
    --- 
    parameters:
        - name: package_name
          in: path
          type: string
          required: true
          description: Name of the package
    responses:
        200:
            description: All feature toggles deleted
        404:
            description: Package not found
    """
    db = MongoConnectionHolder.get_db()
    if db is None:
        return jsonify({'error': 'Database not initialized'}), 500

    package_collection = db[package_name]
    if package_collection is None:
        return jsonify({'error': 'Package not found'}), 404

    # Delete all feature toggles
    package_collection.delete_many({})
    return jsonify({'message': 'All feature toggles deleted'}), 200


# 8. Delete all items
@feature_toggle_blueprint.route('/feature-toggles', methods=['DELETE'])
def delete_all_feature_toggles_all_packages():
    """
    Delete all feature toggles in all packages
    --- 
    responses:
        200:
            description: All feature toggles deleted
    """
    db = MongoConnectionHolder.get_db()
    if db is None:
        return jsonify({'error': 'Database not initialized'}), 500

    # Delete all feature toggles in all packages
    for collection_name in db.list_collection_names():
        db[collection_name].delete_many({})
    return jsonify({'message': 'All feature toggles deleted'}), 200
