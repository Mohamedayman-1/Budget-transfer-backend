from Chatbot.main import orchestrate

def chat_console():
    print("Welcome to the AI Agent Chat! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        print("\n")
        if user_input.strip().lower() in ("exit", "quit"):  # Exit condition
            print("Goodbye!")
            break
        response = orchestrate(user_input, logs=False)
        print("Chatbot:", response,"\n\n")

if __name__ == "__main__":
    chat_console()

