import openai
import os
from models import ConversationAnalysis
import json
from dotenv import load_dotenv

load_dotenv()


class ConversationAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.enabled = True

    async def analyze_conversation(self, conversation_log: str) -> ConversationAnalysis:
        """
        Анализирует разговор продажника с ИИ-клиентом
        """

        prompt = f"""
        Проанализируй разговор продажника с клиентом. Оцени по шкале от 1 до 10:
        
        Разговор:
        {conversation_log}
        
        Верни анализ в формате JSON:
        {{
            "score": <оценка от 1 до 10>,
            "strengths": [<список сильных сторон>],
            "areas_for_improvement": [<области для улучшения>],
            "specific_feedback": "<конкретные рекомендации>",
            "key_moments": [<ключевые моменты разговора>]
        }}
        
        Критерии оценки:
        - Установление контакта с клиентом
        - Выявление потребностей
        - Презентация продукта/услуги
        - Работа с возражениями
        - Закрытие сделки
        - Общее впечатление
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по продажам, анализирующий разговоры продажников. Отвечай только в формате JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            analysis_text = response.choices[0].message.content
            analysis_data = json.loads(analysis_text)

            return ConversationAnalysis(**analysis_data)

        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return self._fallback_analysis(conversation_log)

    def format_analysis_for_display(self, analysis: ConversationAnalysis) -> str:
        """
        Форматирует анализ для отображения на фронтенде
        """

        formatted = f"""
        # 📊 Анализ тренировочной сессии
        
        ## Общая оценка: {analysis.score}/10
        
        ## ✅ Сильные стороны:
        {chr(10).join([f"• {strength}" for strength in analysis.strengths])}
        
        ## 🎯 Области для улучшения:
        {chr(10).join([f"• {area}" for area in analysis.areas_for_improvement])}
        
        ## 💡 Конкретные рекомендации:
        {analysis.specific_feedback}
        
        ## 🔑 Ключевые моменты:
        {chr(10).join([f"• {moment}" for moment in analysis.key_moments])}
        """

        return formatted
