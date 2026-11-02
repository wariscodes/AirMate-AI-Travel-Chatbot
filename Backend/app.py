from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store conversation details temporarily
conversations = {}


# Check whether backend is running
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "message": "Chatbot API is running"
    })


# Identify user request
def detect_intent(message):
    message = message.lower()

    if any(word in message for word in ["cancel", "cancellation"]):
        return "cancel"

    if any(word in message for word in ["change", "modify", "reschedule"]):
        return "change"

    if any(word in message for word in ["book", "booking", "reserve"]):
        return "book"

    return "unknown"


# Questions for each request
questions = {
    "book": {
        "departure": "Which city are you departing from?",
        "destination": "Where would you like to go?",
        "date": "What is your travel date?",
        "passengers": "How many passengers will travel?"
    },
    "cancel": {
        "booking_reference": "Please provide your booking reference."
    },
    "change": {
        "booking_reference": "Please provide your booking reference.",
        "new_date": "What is your new travel date?"
    }
}


# Return the next question
def get_question(intent, step):
    return questions[intent][step]


# Intent prediction endpoint
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "error": "Please enter a message"
        }), 400

    intent = detect_intent(message)

    return jsonify({
        "message": message,
        "intent": intent
    })


# Main chatbot endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id", "default")

    if not message:
        return jsonify({
            "reply": "Please enter your request."
        }), 400

    # Create conversation if it does not exist
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "intent": None,
            "step": None,
            "details": {}
        }

    conversation = conversations[conversation_id]

    # Identify intent
    if conversation["intent"] is None:

        intent = detect_intent(message)

        if intent == "unknown":
            reply = (
                "I can help with flight booking, cancellation, "
                "or changing a booking. What would you like to do?"
            )

        else:
            conversation["intent"] = intent
            conversation["details"] = {}

            if intent == "book":
                conversation["step"] = "departure"

            elif intent == "cancel":
                conversation["step"] = "booking_reference"

            else:
                conversation["step"] = "booking_reference"

            reply = get_question(
                intent,
                conversation["step"]
            )

    else:

        # Save user's answer
        current_step = conversation["step"]

        conversation["details"][current_step] = message

        intent = conversation["intent"]

        # Define question order
        if intent == "book":
            steps = [
                "departure",
                "destination",
                "date",
                "passengers"
            ]

        elif intent == "cancel":
            steps = [
                "booking_reference"
            ]

        else:
            steps = [
                "booking_reference",
                "new_date"
            ]

        # Find next question
        current_index = steps.index(current_step)

        if current_index + 1 < len(steps):

            next_step = steps[current_index + 1]

            conversation["step"] = next_step

            reply = get_question(
                intent,
                next_step
            )

        else:

            details = conversation["details"]

            # Prepare booking request
            if intent == "book":

                reply = (
                    "Your flight request has been prepared!\n\n"
                    f"Departure: {details['departure']}\n"
                    f"Destination: {details['destination']}\n"
                    f"Travel Date: {details['date']}\n"
                    f"Passengers: {details['passengers']}\n\n"
                    "This is a prototype. No actual ticket has been booked."
                )

            # Prepare cancellation request
            elif intent == "cancel":

                reply = (
                    "Your cancellation request has been prepared.\n\n"
                    f"Booking Reference: "
                    f"{details['booking_reference']}\n\n"
                    "No actual flight has been cancelled."
                )

            # Prepare change request
            else:

                reply = (
                    "Your flight change request has been prepared.\n\n"
                    f"Booking Reference: "
                    f"{details['booking_reference']}\n"
                    f"New Travel Date: {details['new_date']}\n\n"
                    "No actual flight has been changed."
                )

            # Reset conversation after completion
            conversation["intent"] = None
            conversation["step"] = None
            conversation["details"] = {}

    return jsonify({
        "reply": reply,
        "intent": conversation["intent"],
        "complete": conversation["step"] is None
    })


# Start Flask server
if __name__ == "__main__":
    app.run(debug=True)
