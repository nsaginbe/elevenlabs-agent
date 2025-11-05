import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
agent_id = os.getenv("ELEVENLABS_AGENT_ID")
client = ElevenLabs(api_key=api_key)


def build_session_system_prompt(
    company_description: str = "",
    difficulty_level: str = "Средний",
) -> str:
    
    base_prompt = get_system_prompt()

    dynamic_params = (
        "\n\n=== ДИНАМИЧЕСКИЕ ПАРАМЕТРЫ СЕССИИ ===\n"
        f"product_description: \"{company_description}\"\n"
        f"difficulty_level: \"{difficulty_level}\"\n"
    )

    return f"{base_prompt}{dynamic_params}"


def get_system_prompt() -> str:
    agent = client.conversational_ai.agents.get(agent_id=agent_id)
    return agent.conversation_config.agent.prompt.prompt


# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         prompt = get_system_prompt()
#         print("System Prompt:")
#         print(prompt)
    
#     asyncio.run(main())