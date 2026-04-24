
# from flask import Flask, jsonify, request, make_response
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# from flask_bcrypt import Bcrypt
# from flask_jwt_extended import JWTManager
# from flask_cors import CORS
# from flask_mail import Mail
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# db = SQLAlchemy()
# migrate = Migrate()
# bcrypt = Bcrypt()
# jwt = JWTManager()
# mail = Mail()

# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )

# def create_app():
#     app = Flask(__name__)
#     app.url_map.strict_slashes = False

#     # ================= CONFIG =================
#     from config.config import Config
#     app.config.from_object(Config)

#     # ================= EXTENSIONS =================
#     db.init_app(app)
#     migrate.init_app(app, db)
#     bcrypt.init_app(app)
#     jwt.init_app(app)
#     mail.init_app(app)
#     limiter.init_app(app)

#     # ================= INTERCEPT OPTIONS FIRST =================
#     @app.before_request
#     def handle_options():
#         if request.method == "OPTIONS":
#             return make_response("", 204)

#     # ================= CORS =================
#     CORS(
#         app,
#         supports_credentials=True,
#         origins=[
#             "http://localhost:3000",
#             "http://127.0.0.1:3000",
#             "http://localhost:3001",
#             "http://127.0.0.1:3001",
#             "http://localhost:3005",
#             "http://127.0.0.1:3005",
#             "http://localhost:5173",
#             "http://127.0.0.1:5173"
#         ],
#         allow_headers=["Content-Type", "Authorization"],
#         expose_headers=["Content-Type", "Authorization"],
#         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
#     )

#     # ================= MODELS =================
#     from models import User, Doctor, Patient, Admin
#     from models.email_verification import EmailVerification
#     from models.password_reset_token import PasswordResetToken
#     from models.scan import Scan

#     # ================= BLUEPRINTS =================
#     from routes.auth import auth_bp
#     from routes.admin import admin_bp
#     from routes.account import account_bp
#     from routes.assignment import assignment_bp
#     from routes.scan import scan_bp
#     from routes.profile import profile_bp


#     app.register_blueprint(auth_bp)
#     app.register_blueprint(admin_bp)
#     app.register_blueprint(account_bp)
#     app.register_blueprint(assignment_bp)
#     app.register_blueprint(scan_bp)
#     app.register_blueprint(profile_bp)
#     # DEBUG: Print all routes
#     print("\n=== REGISTERED ROUTES ===")
#     for rule in app.url_map.iter_rules():
#         print(f"{rule.endpoint:30s} {rule.methods} {rule}")
#     print("=========================\n")

#     # ================= ERROR HANDLERS =================
#     @app.errorhandler(429)
#     def rate_limit_exceeded(e):
#         return jsonify({
#             "success": False,
#             "message": "Too many attempts. Please try again later."
#         }), 429

#     @app.errorhandler(404)
#     def not_found(e):
#         return jsonify({
#             "success": False,
#             "message": "Route not found."
#         }), 404

#     @app.errorhandler(500)
#     def server_error(e):
#         return jsonify({
#             "success": False,
#             "message": "Internal server error."
#         }), 500

#     return app






# import os
# import redis
# from flask import Flask, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# from flask_bcrypt import Bcrypt
# from flask_jwt_extended import JWTManager
# from flask_cors import CORS
# from flask_mail import Mail
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# db      = SQLAlchemy()
# migrate = Migrate()
# bcrypt  = Bcrypt()
# jwt     = JWTManager()
# mail    = Mail()
# limiter = Limiter(
#     key_func       = get_remote_address,
#     default_limits = ["200 per day", "50 per hour"]
# )

# # ── Redis client (Upstash) ────────────────────────────────
# redis_client = redis.from_url(
#     os.getenv("REDIS_URL"),
#     decode_responses = True    # returns strings not bytes
# )


# def create_app():
#     app = Flask(__name__)

#     from config.config import Config
#     app.config.from_object(Config)

#     db.init_app(app)
#     migrate.init_app(app, db)
#     bcrypt.init_app(app)
#     jwt.init_app(app)
#     CORS(app, supports_credentials=True)
#     mail.init_app(app)
#     limiter.init_app(app)

#     # ── JWT blacklist checker ─────────────────────────────
#     @jwt.token_in_blocklist_loader
#     def check_if_token_revoked(jwt_header, jwt_payload):
#         jti = jwt_payload["jti"]
#         return redis_client.get(f"blacklist:{jti}") is not None

#     # Import all models
#     from models import User, Doctor, Patient, Admin
#     from models.email_verification import EmailVerification
#     from models.password_reset_token import PasswordResetToken
#     from models.doctor_assignment import DoctorAssignment
#     from models.scan import Scan

#     # Register blueprints
#     from routes.auth import auth_bp
#     from routes.admin import admin_bp
#     from routes.account import account_bp
#     from routes.assignment import assignment_bp
#     from routes.scan import scan_bp
#     from routes.profile import profile_bp

#     app.register_blueprint(auth_bp)
#     app.register_blueprint(admin_bp)
#     app.register_blueprint(account_bp)
#     app.register_blueprint(assignment_bp)
#     app.register_blueprint(scan_bp)
#     app.register_blueprint(profile_bp)

#     # Global error handlers
#     @app.errorhandler(429)
#     def rate_limit_exceeded(e):
#         return jsonify({"success": False, "message": "Too many attempts. Please wait and try again."}), 429

#     @app.errorhandler(404)
#     def not_found(e):
#         return jsonify({"success": False, "message": "Route not found."}), 404

#     @app.errorhandler(500)
#     def server_error(e):
#         return jsonify({"success": False, "message": "Internal server error."}), 500

#     return app




from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import os
import redis
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ================= REDIS (ADDED SAFELY) =================
redis_url = os.getenv("REDIS_URL")

if redis_url:
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        print("✅ Redis connected")
    except Exception as e:
        print("⚠️ Redis connection failed:", e)
        redis_client = None
else:
    print("⚠️ REDIS_URL not set")
    redis_client = None


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # ================= CONFIG =================
    from config.config import Config
    app.config.from_object(Config)

    # ================= EXTENSIONS =================
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ================= INTERCEPT OPTIONS FIRST =================
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            return make_response("", 204)

    # ================= CORS =================
    CORS(
        app,
        supports_credentials=True,
        origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3005",
            "http://127.0.0.1:3005",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # ================= MODELS =================
    from models import User, Doctor, Patient, Admin
    from models.email_verification import EmailVerification
    from models.password_reset_token import PasswordResetToken
    # from models.scan import Scan
    from models.detection_scan import DetectionScan, MultimodalResult

    # ================= REDIS USAGE EXAMPLE (OPTIONAL SAFETY) =================
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]

        if redis_client:
            return redis_client.get(f"blacklist:{jti}") is not None

        return False

    # ================= BLUEPRINTS =================
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.account import account_bp
    from routes.assignment import assignment_bp
    from routes.scan import detection_bp
    from routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(assignment_bp)
    # app.register_blueprint(scan_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(profile_bp)

    # DEBUG: Print all routes
    print("\n=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} {rule.methods} {rule}")
    print("=========================\n")

    # ================= ERROR HANDLERS =================
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            "success": False,
            "message": "Too many attempts. Please try again later."
        }), 429

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "message": "Route not found."
        }), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    return app