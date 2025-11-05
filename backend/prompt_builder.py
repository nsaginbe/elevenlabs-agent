"""
Модуль для формирования итогового system prompt на основе шаблона и настроек
"""


def build_final_prompt(
    company_description: str = "",
    difficulty_level: str = "",
) -> str:
    """
    Формирует итоговый system prompt, подставляя значения из настроек в шаблон.
    
    Args:
        company_description: Описание компании/продукта
        difficulty_level: Уровень сложности (Лёгкий, Средний, Сложный, Экспертный)
    
    Returns:
        Итоговый системный промпт для агента
    """
    
    # Если шаблон не задан, используем базовый шаблон
    system_prompt_template = get_default_prompt_template()
    
    # Определяем характеристики сложности
    difficulty_characteristics = get_difficulty_characteristics(difficulty_level)
    
    # Формируем итоговый промпт
    final_prompt = system_prompt_template
    
    # Подставляем описание компании
    if company_description:
        final_prompt = final_prompt.replace("{company_description}", company_description)
        final_prompt = final_prompt.replace("{{company_description}}", company_description)
    else:
        final_prompt = final_prompt.replace("{company_description}", "продукт или услуга")
        final_prompt = final_prompt.replace("{{company_description}}", "продукт или услуга")
    
    # Подставляем уровень сложности и его характеристики
    if difficulty_level:
        final_prompt = final_prompt.replace("{difficulty_level}", difficulty_level)
        final_prompt = final_prompt.replace("{{difficulty_level}}", difficulty_level)
        final_prompt = final_prompt.replace("{difficulty_characteristics}", difficulty_characteristics)
        final_prompt = final_prompt.replace("{{difficulty_characteristics}}", difficulty_characteristics)
    else:
        final_prompt = final_prompt.replace("{difficulty_level}", "Средний")
        final_prompt = final_prompt.replace("{{difficulty_level}}", "Средний")
        final_prompt = final_prompt.replace("{difficulty_characteristics}", "умеренно сложные возражения")
        final_prompt = final_prompt.replace("{{difficulty_characteristics}}", "умеренно сложные возражения")
    
    # Очищаем незаполненные плейсхолдеры
    import re
    final_prompt = re.sub(r'\{[^}]+\}', '', final_prompt)
    final_prompt = re.sub(r'\{\{[^}]+\}\}', '', final_prompt)
    
    return final_prompt.strip()


def get_difficulty_characteristics(difficulty_level: str) -> str:
    """
    Возвращает характеристики поведения клиента в зависимости от уровня сложности.
    """
    characteristics = {
        "Лёгкий": (
            "Проявляет интерес к продукту, задает простые вопросы, "
            "минимальные возражения, готов к покупке. Отвечай дружелюбно и помогай "
            "сделать выбор без давления."
        ),
        "Средний": (
            "Задает уточняющие вопросы, имеет некоторые сомнения, "
            "выражает умеренные возражения по цене или качеству. "
            "Требует убедительных аргументов и дополнительной информации."
        ),
        "Сложный": (
            "Скептически настроен, задает сложные вопросы, "
            "выражает серьезные возражения. Сравнивает с конкурентами, "
            "сомневается в ценности предложения. Требует высокого уровня "
            "убеждения и работы с возражениями."
        ),
        "Экспертный": (
            "Очень опытный покупатель, задает экспертные вопросы, "
            "выражает сложные технические возражения. Знает рынок и конкурентов, "
            "может быть агрессивен. Требует профессионального подхода, "
            "доказательств ценности и мастерского закрытия сделки."
        ),
    }
    
    return characteristics.get(difficulty_level, characteristics["Средний"])


def get_default_prompt_template() -> str:
    """
    Возвращает базовый шаблон системного промпта.
    Этот шаблон можно будет заменить из документа System_Prompt_MoonAI_v2.
    """
    return """Ты - ИИ-клиент для тренировки навыков продаж.

Твоя роль:
- Имитировать реального клиента, который интересуется {company_description}
- Уровень сложности: {difficulty_level}
- Характеристики поведения: {difficulty_characteristics}

Правила поведения:
1. Веди себя естественно, как настоящий клиент
2. Задавай вопросы о продукте/услуге
3. Выражай возражения в соответствии с уровнем сложности
4. Не соглашайся сразу - давай продавцу возможность отработать навыки
5. Скажи "Завершить" когда продавец закончит презентацию

Контекст компании:
{company_description}

Помни: твоя цель - помочь продавцу улучшить навыки продаж через реалистичную симуляцию."""
