from localbot.ml_intent import get_intent
import aiml
import os

kernel = aiml.Kernel()

AIML_PATH = os.path.join(os.path.dirname(__file__), "aiml_files")

for file in os.listdir(AIML_PATH):
    if file.endswith(".aiml"):
        kernel.learn(os.path.join(AIML_PATH, file))


def get_aiml_response(message):
    if not message:
        return "Please say something 🙂"

    message = message.upper().strip()

    # 1️⃣ AIML FIRST
    response = kernel.respond(message)
    if response and "not sure" not in response.lower():
        return response

    # 2️⃣ ML FALLBACK
    intent = get_intent(message.lower())

    if intent == "add_vendor":
        return "You can add vendors using the Add Vendor page or WhatsApp. Want steps?"

    if intent == "about_platform":
        return "Hidden Local helps discover underrated local vendors around you."

    if intent == "greeting":
        return "Hi 👋 I’m LocalBot. Ask me anything about Hidden Local!"

    # 3️⃣ DEFAULT
    return "I’m still learning 🤖 Try asking about vendors or features."
