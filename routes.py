from controllers.feature_toggle import feature_toggle_blueprint
from controllers import health_controller
from flask import jsonify, request




def init_routes(app):
    app.register_blueprint(feature_toggle_blueprint)
        # --- FitCheck: Health ---
    def health():
        return jsonify({"status": "ok", "service": "FitCheck Insights API"}), 200

    app.add_url_rule(
        "/health",
        view_func=health,
        methods=["GET"]
    )

        # --- FitCheck: Config ---
    def get_config():
        config = {
            "steps_goal_daily": 10000,
            "sleep_min_hours": 7.0,
            "calories_recommended": 2200
        }
        return jsonify(config), 200

    app.add_url_rule(
        "/config",
        view_func=get_config,
        methods=["GET"]
    )


        # --- FitCheck: Insights Evaluate ---
    def evaluate_insights():
        """
        Expected JSON:
        {
          "weight": 76.5,
          "steps": 8700,
          "sleepHours": 6.3,
          "calories": 2100
        }
        """
        data = request.get_json(silent=True) or {}

        required = ["weight", "steps", "sleepHours", "calories"]
        missing = [k for k in required if k not in data]
        if missing:
            return jsonify({"error": f"missing fields: {missing}"}), 400

        try:
            weight = float(data["weight"])
            steps = int(data["steps"])
            sleep_hours = float(data["sleepHours"])
            calories = int(data["calories"])
        except (TypeError, ValueError):
            return jsonify({"error": "invalid types; expected numbers for all fields"}), 400

        # תובנות בסיסיות
        CONFIG = {
            "steps_goal_daily": 10000,
            "sleep_min_hours": 7.0,
            "calories_recommended": 2200
        }

        insights = []

        # 1️⃣ עמידה ביעד צעדים
        met_steps_goal = steps >= CONFIG["steps_goal_daily"]
        insights.append({
            "key": "daily_steps_goal",
            "ok": met_steps_goal,
            "message": "Great! You hit your daily steps goal."
                       if met_steps_goal
                       else f"You're {CONFIG['steps_goal_daily'] - steps} steps short of today's goal."
        })

        # 2️⃣ איכות שינה
        good_sleep = sleep_hours >= CONFIG["sleep_min_hours"]
        insights.append({
            "key": "sleep_quality",
            "ok": good_sleep,
            "message": "Sleep looks solid for training."
                       if good_sleep
                       else f"Consider lighter training or rest – you slept {sleep_hours}h (< {CONFIG['sleep_min_hours']}h)."
        })

        # 3️⃣ יום מנוחה
        rest_day = sleep_hours < CONFIG["sleep_min_hours"]
        insights.append({
            "key": "rest_day_recommendation",
            "ok": not rest_day,
            "message": "Recommended rest or light activity today."
                       if rest_day
                       else "No rest day needed based on sleep alone."
        })

        # 4️⃣ קלוריות
        diff_cal = calories - CONFIG["calories_recommended"]
        if abs(diff_cal) <= 150:
            cal_msg = "On target."
        elif diff_cal > 150:
            cal_msg = "Slightly above recommended."
        else:
            cal_msg = "Slightly below recommended."

        insights.append({
            "key": "calories_delta",
            "ok": True,
            "message": f"Calories: {calories} vs rec {CONFIG['calories_recommended']}. {cal_msg}"
        })

        return jsonify({
            "summary": {
                "met_steps_goal": met_steps_goal,
                "good_sleep": good_sleep,
                "rest_day": rest_day
            },
            "insights": insights
        }), 200

    app.add_url_rule(
        "/insights/evaluate",
        view_func=evaluate_insights,
        methods=["POST"]
    )



   