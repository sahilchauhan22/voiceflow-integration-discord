import os
import discord
import requests

# Add at the top
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

@app.route('/launch', methods=['POST'])
def launch_bot():
    user_id = request.json.get("user_id", "test_user")
    message = request.json.get("message", "launch")
    response = get_voiceflow_response(user_id, message)
    return jsonify({"response": response})

# Run Flask server in a separate thread
def run_flask():
    app.run(port=5000)

threading.Thread(target=run_flask).start()


# Discord bot token
DISCORD_TOKEN = "Paste your discord token here which u will get while making discord bot"
# Voiceflow API key
VOICEFLOW_API_KEY = "Paste your voiceflow API key"
# Voiceflow Project ID
PROJECT_ID = "paste your project id of voiceflow here"
PROJECT_VERSION_ID = "paste your project version id of voiceflow here"


# Set up Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Required for newer versions
client = discord.Client(intents=intents)

# Function to send message to Voiceflow and get response
def get_voiceflow_response(user_id, message):
    url = f"https://general-runtime.voiceflow.com/state/user/{user_id}/interact?versionID={PROJECT_VERSION_ID}"
    headers = {
        "Authorization": VOICEFLOW_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "action": {
            "type": "text",
            "payload": message
        },
        "config": {
            "tts": False,
            "stripSSML": True,
            "stopAll": False,
            "excludeTypes": ["block", "debug", "flow"]
        }
    }

    print(f"Sending to Voiceflow: {payload}")  # 🟡 Debug
    response = requests.post(url, headers=headers, json=payload)

    print(f"Voiceflow Status Code: {response.status_code}")  # 🟡 Debug
    print(f"Voiceflow Raw Response: {response.text}")         # 🟡 Debug

    if response.status_code == 200:
        data = response.json()
        if data:
            messages = []
            for trace in data:

               if trace["type"] == "text":

                if isinstance(trace.get("payload"), dict) and "message" in trace["payload"]:

                 messages.append(trace["payload"]["message"])
               elif isinstance(trace.get("payload"), str):
                messages.append(trace["payload"])

               elif trace["type"] == "choice":
                choices = [button["name"] for button in trace["payload"]["buttons"]]
                messages.append("Options: " + ", ".join(choices))

            return "\n".join(messages) if messages else "I'm not sure how to respond to that."
    
# Discord bot event handlers
@client.event
async def on_ready():
    print(f'✅ {client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Ignore bot's own messages

    user_id = str(message.author.id)
    
    # Send user message to Voiceflow and get response
    response = get_voiceflow_response(user_id, message.content)

    # Send Voiceflow response back to Discord
    await message.channel.send(response)

# Run the bot
client.run(DISCORD_TOKEN)
