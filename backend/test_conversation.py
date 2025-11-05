import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def main():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    agent_id = os.getenv("ELEVENLABS_AGENT_ID")

    from elevenlabs.client import ElevenLabs  # type: ignore
    from elevenlabs.conversational_ai.conversation import Conversation
    from elevenlabs.conversational_ai.audio_interface import DefaultAudioInterface


    elevenlabs_client = ElevenLabs(api_key=api_key)

    # Колбэки печатают прогресс в консоль
    def on_agent_response(response: str):
        print(f"Agent: {response}")

    def on_agent_response_correction(original: str, corrected: str):
        print(f"Agent: {original} -> {corrected}")

    def on_user_transcript(transcript: str):
        print(f"User: {transcript}")

    # Формируем разговорную сессию (микрофон/аудио по умолчанию)
    conversation = Conversation(
        elevenlabs_client,
        agent_id,
        requires_auth=bool(api_key),
        audio_interface=DefaultAudioInterface(),
        callback_agent_response=on_agent_response,
        callback_agent_response_correction=on_agent_response_correction,
        callback_user_transcript=on_user_transcript,
        # callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
    )

    print("Starting conversation. Press Ctrl+C to stop.")
    try:
        await conversation.start()
        # Держим соединение, пока пользователь не завершит
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping conversation...")
    finally:
        try:
            await conversation.stop()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())


