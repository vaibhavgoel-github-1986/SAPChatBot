from Workflows.SAPAgent import start_chatbot

def main():

    # Start the chatbot
    print("Starting the Chatbot...")
    try:
        start_chatbot()
    except KeyboardInterrupt:
        print("\nChatbot terminated by user.")


if __name__ == "__main__":
    main()
