from controllers.feature_toggle import feature_toggle_blueprint

def init_routes(app):
    app.register_blueprint(feature_toggle_blueprint)