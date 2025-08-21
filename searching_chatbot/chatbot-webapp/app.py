import os
import random
import textwrap
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "please_change_me")

# Database imports
from models import SessionLocal, Conversation, Message, Base, engine
Base.metadata.create_all(bind=engine)  # create tables if not exist

# Default settings
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
STICKERS = ["🤖", "😊", "🔥", "🎉", "💡", "🚀", "✨", "📚", "😎"]

# Groq SDK availability
try:
    from groq import Groq
    import groq as groq_module
    GroqAvailable = True
except Exception:
    GroqAvailable = False
    groq_module = None

# ---------------- Functions ----------------
def call_groq_safe(messages_for_llm, model=DEFAULT_MODEL):
    """Return (assistant_text, error_code)"""
    if not GroqAvailable:
        return "(Fallback) Groq SDK not installed.", "no_sdk"

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "(Fallback) GROQ_API_KEY not set.", "no_key"

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=messages_for_llm,
            max_tokens=250,
            temperature=0.7
        )
        assistant_text = completion.choices[0].message.content.strip()
        return assistant_text, None
    except Exception as e:
        try:
            AuthErr = getattr(groq_module, "AuthenticationError", None)
            if AuthErr and isinstance(e, AuthErr):
                return "(Fallback) Authentication failed: invalid API key.", "auth"
        except Exception:
            pass
        if "invalid_api_key" in str(e) or "Invalid API Key" in str(e):
            return "(Fallback) Authentication failed: invalid API key.", "auth"
        return f"(Fallback) Groq error: {str(e)}", "error"

def ensure_session():
    """Ensure session ID exists"""
    if 'sid' not in session:
        session['sid'] = f"s_{random.getrandbits(64):016x}"
    return session['sid']

# ---------------- Routes ----------------
@app.route("/", methods=["GET"])
def index():
    sid = ensure_session()
    db = SessionLocal()
    # Load last conversation messages
    conv = db.query(Conversation).filter_by(session_id=sid).order_by(Conversation.id.desc()).first()
    messages = []
    if conv:
        msgs = db.query(Message).filter_by(conversation_id=conv.id).order_by(Message.id.asc()).all()
        for m in msgs:
            messages.append({"role": m.role, "content": m.content})
    db.close()
    return render_template("index.html", messages=messages)

@app.route("/send", methods=["POST"])
def send():
    sid = ensure_session()
    text = (request.form.get("message") or "").strip()
    if not text:
        return jsonify(reply="Please type a message.")

    db = SessionLocal()
    conv = db.query(Conversation).filter_by(session_id=sid).order_by(Conversation.id.desc()).first()
    if not conv:
        conv = Conversation(session_id=sid)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=text)
    db.add(user_msg)
    db.commit()

    # Build messages for LLM
    system_prompt = "You are a helpful assistant. Detect the user's language and reply quickly in the same language."
    msgs = db.query(Message).filter_by(conversation_id=conv.id).order_by(Message.id.asc()).all()
    messages_for_llm = [{"role": "system", "content": system_prompt}] + [{"role": m.role, "content": m.content} for m in msgs]

    # Call Groq (or fallback)
    assistant_text, err = call_groq_safe(messages_for_llm)

    # Save assistant reply
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)
    db.commit()
    db.close()

    # Add sticker if normal
    if err is None:
        display = f"{random.choice(STICKERS)} {textwrap.fill(assistant_text, width=80)}"
    else:
        display = assistant_text

    return jsonify(reply=display)

@app.route("/clear", methods=["POST"])
def clear_conv():
    sid = ensure_session()
    db = SessionLocal()
    convs = db.query(Conversation).filter_by(session_id=sid).all()
    for c in convs:
        db.delete(c)
    db.commit()
    db.close()
    return jsonify(status="ok")

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
