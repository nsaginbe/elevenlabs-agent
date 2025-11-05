"""
Модуль для работы с ElevenLabs API для обновления system prompt агента
"""

import os
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class ElevenLabsClient:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID")
    
    async def update_agent_system_prompt(self, system_prompt: str) -> bool:
        """
        Обновляет system prompt агента через ElevenLabs API.
        
        Args:
            system_prompt: Новый системный промпт для агента
        
        Returns:
            True если успешно, False в противном случае
        """
        if not self.api_key or not self.agent_id:
            print("Warning: ElevenLabs API key or Agent ID not configured")
            return False
        
        try:
            # Получаем текущую конфигурацию агента
            async with httpx.AsyncClient() as client:
                # Получаем информацию об агенте
                response = await client.get(
                    f"{self.base_url}/convai/agents/{self.agent_id}",
                    headers={"xi-api-key": self.api_key},
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    print(f"Failed to get agent: {response.status_code}")
                    return False
                
                agent_data = response.json()
                
                # Обновляем system prompt в конфигурации
                agent_data["system_prompt"] = system_prompt
                
                # Обновляем агента
                update_response = await client.patch(
                    f"{self.base_url}/convai/agents/{self.agent_id}",
                    headers={"xi-api-key": self.api_key},
                    json=agent_data,
                    timeout=10.0,
                )
                
                if update_response.status_code in [200, 204]:
                    print(f"Successfully updated agent system prompt")
                    return True
                else:
                    print(f"Failed to update agent: {update_response.status_code}")
                    print(f"Response: {update_response.text}")
                    return False
                    
        except Exception as e:
            print(f"Error updating ElevenLabs agent: {e}")
            return False
    
    async def get_agent_system_prompt(self) -> Optional[str]:
        """
        Получает текущий system prompt агента.
        
        Returns:
            System prompt или None в случае ошибки
        """
        if not self.api_key or not self.agent_id:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/convai/agents/{self.agent_id}",
                    headers={"xi-api-key": self.api_key},
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    agent_data = response.json()
                    return agent_data.get("system_prompt", "")
                else:
                    print(f"Failed to get agent: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error getting ElevenLabs agent: {e}")
            return None


if __name__ == "__main__":
    import asyncio
    async def main():
        elevenlabs_client = ElevenLabsClient()
        system_prompt = await elevenlabs_client.get_agent_system_prompt()
        print(system_prompt, "system_prompt")
    asyncio.run(main())