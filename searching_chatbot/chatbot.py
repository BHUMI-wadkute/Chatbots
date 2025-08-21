import sys
import random
import textwrap
import time
from groq import Groq
from colorama import Fore, Style, init

# Initialize colorama for Windows terminal color support
init(autoreset=True)

# Set stdout to UTF-8 (for Hindi & other languages)
sys.stdout.reconfigure(encoding='utf-8')

# Initialize Groq Client
client = Groq(api_key='GROQ_API_KEY')

# Stickers / Emojis for fun responses
stickers = ["🤖", "😊", "🔥", "🎉", "💡", "🚀", "✨", "📚", "😎"]

# Conversation history
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant. "
            "giving all replys friendly and techinical answers. "
            "Detect the user's language and respond in the same language. "
            "If the language is mixed, respond in the primary language of the question."
        )
    }
]

print(Fore.CYAN + "=" * 60)
print(Fore.GREEN + "🤖 Chatbot ")
print(Fore.CYAN + "=" * 60)

while True:
    # Get user input
    user_input = input(Fore.YELLOW + "\nYou: " + Style.RESET_ALL)

    if user_input.lower() == "quit":
        print(Fore.RED + "\n🔴 Chatbot ended. Goodbye! 👋")
        break

    # Add user message to history
    messages.append({"role": "user", "content": user_input})

    # Show typing effect
    print(Fore.MAGENTA + "\nBot is typing", end="")
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print("\n")

    # Get response from Groq API
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile"
    )

    # Extract assistant reply
    reply = chat_completion.choices[0].message.content

    # Wrap long text (80 characters per line)
    formatted_reply = textwrap.fill(reply, width=80)

    # Add random emoji sticker
    sticker = random.choice(stickers)

    # Print nicely
    print(Fore.CYAN + "-" * 60)
    print(Fore.GREEN + f"Roz {sticker}:\n" + Fore.WHITE + formatted_reply)
    print(Fore.CYAN + "-" * 60)

    # Add assistant reply to history
    messages.append({"role": "assistant", "content": reply})
