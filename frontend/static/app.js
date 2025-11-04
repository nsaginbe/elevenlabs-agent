class SalesTrainingApp {
    constructor() {
        this.currentSession = null;
        this.conversationStarted = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSessionHistory();
        this.setupConvAIListeners();
    }

    bindEvents() {
        const startBtn = document.getElementById('startTraining');
        const stopBtn = document.getElementById('stopTraining');
        const managerNameInput = document.getElementById('managerName');

        startBtn.addEventListener('click', () => this.startTraining());
        stopBtn.addEventListener('click', () => this.stopTraining());
        
        // Закрытие модального окна
        const modal = document.getElementById('analysisModal');
        const closeBtn = modal.querySelector('.close');
        
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });

        // Enter для начала тренировки
        managerNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !startBtn.disabled) {
                this.startTraining();
            }
        });
    }

    async startTraining() {
        const managerName = document.getElementById('managerName').value.trim();
        
        if (!managerName) {
            alert('Пожалуйста, введите ваше имя');
            return;
        }

        try {
            const response = await fetch('/api/sessions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ manager_name: managerName })
            });

            if (!response.ok) {
                throw new Error('Ошибка создания сессии');
            }

            this.currentSession = await response.json();
            this.showTrainingInterface();
            this.updateSessionInfo();

        } catch (error) {
            console.error('Ошибка запуска тренировки:', error);
            alert('Не удалось запустить тренировку. Попробуйте еще раз.');
        }
    }

    async stopTraining() {
        if (!this.currentSession) return;

        try {
            // Завершаем сессию
            const response = await fetch(`/api/sessions/${this.currentSession.id}/complete`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_log: this.getConversationLog()
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка завершения сессии');
            }

            const completedSession = await response.json();
            this.hideTrainingInterface();
            this.showAnalysis(completedSession);
            this.loadSessionHistory();

        } catch (error) {
            console.error('Ошибка завершения тренировки:', error);
            alert('Не удалось завершить тренировку. Попробуйте еще раз.');
        }
    }

    showTrainingInterface() {
        document.getElementById('startTraining').style.display = 'none';
        document.getElementById('stopTraining').style.display = 'inline-flex';
        document.getElementById('managerName').disabled = true;
        document.getElementById('sessionInfo').style.display = 'block';
        document.getElementById('convaiContainer').style.display = 'block';
    }

    hideTrainingInterface() {
        document.getElementById('startTraining').style.display = 'inline-flex';
        document.getElementById('stopTraining').style.display = 'none';
        document.getElementById('managerName').disabled = false;
        document.getElementById('sessionInfo').style.display = 'none';
        document.getElementById('convaiContainer').style.display = 'none';
        
        this.currentSession = null;
        this.conversationStarted = false;
    }

    updateSessionInfo() {
        if (!this.currentSession) return;

        document.getElementById('sessionId').textContent = this.currentSession.id;
        document.getElementById('sessionStart').textContent = 
            new Date(this.currentSession.session_start).toLocaleString('ru-RU');
        
        const statusElement = document.getElementById('sessionStatus');
        statusElement.textContent = 'Активна';
        statusElement.className = 'status active';
    }

    setupConvAIListeners() {
        // Слушаем события от ElevenLabs ConvAI
        window.addEventListener('message', (event) => {
            if (event.data.type === 'convai-started') {
                this.conversationStarted = true;
                console.log('Разговор начат');
            }
            
            if (event.data.type === 'convai-ended') {
                console.log('Разговор завершен');
                // Автоматически завершаем тренировку если было стоп-слово
                if (event.data.reason === 'stop-word') {
                    setTimeout(() => this.stopTraining(), 1000);
                }
            }
        });
    }

    getConversationLog() {
        // В реальном приложении здесь должен быть лог разговора
        // Для демо возвращаем заглушку
        return `Тренировочная сессия с ${this.currentSession.manager_name}
Начало: ${new Date(this.currentSession.session_start).toLocaleString('ru-RU')}
Конец: ${new Date().toLocaleString('ru-RU')}

Примечание: Логирование разговоров требует дополнительной настройки ElevenLabs API.`;
    }

    async loadSessionHistory() {
        try {
            const response = await fetch('/api/sessions/');
            if (!response.ok) return;

            const sessions = await response.json();
            this.displaySessionHistory(sessions);

        } catch (error) {
            console.error('Ошибка загрузки истории:', error);
        }
    }

    displaySessionHistory(sessions) {
        const historyContainer = document.getElementById('sessionHistory');
        
        if (sessions.length === 0) {
            historyContainer.innerHTML = '<p class="no-sessions">Пока нет завершенных сессий</p>';
            return;
        }

        const completedSessions = sessions.filter(s => s.status === 'analyzed' || s.status === 'completed');
        
        if (completedSessions.length === 0) {
            historyContainer.innerHTML = '<p class="no-sessions">Пока нет завершенных сессий</p>';
            return;
        }

        historyContainer.innerHTML = completedSessions.map(session => `
            <div class="history-item" onclick="window.location.href='/api/sessions/${session.id}/analysis'">
                <h4>${session.manager_name}</h4>
                <div class="meta">
                    <div>${new Date(session.session_start).toLocaleString('ru-RU')}</div>
                    ${session.score ? `<div>Оценка: ${session.score}/10</div>` : ''}
                </div>
            </div>
        `).join('');
    }

    async showAnalysis(session) {
        const modal = document.getElementById('analysisModal');
        const content = document.getElementById('analysisContent');
        
        // Показываем модал с загрузкой
        content.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                Анализируем вашу тренировку...
            </div>
        `;
        modal.style.display = 'flex';

        // Ждем завершения анализа
        let attempts = 0;
        const maxAttempts = 30; // 30 секунд
        
        const checkAnalysis = async () => {
            try {
                const response = await fetch(`/api/sessions/${session.id}`);
                const updatedSession = await response.json();
                
                if (updatedSession.status === 'analyzed') {
                    // Показываем результат анализа
                    content.innerHTML = `
                        <h2>🎯 Анализ завершен!</h2>
                        <div style="margin: 20px 0;">
                            <strong>Оценка: ${updatedSession.score}/10</strong>
                        </div>
                        <p>Подробный анализ доступен на отдельной странице.</p>
                        <div style="margin-top: 30px; text-align: center;">
                            <a href="/api/sessions/${session.id}/analysis" class="btn btn-primary">
                                <i class="fas fa-chart-line"></i> Посмотреть подробный анализ
                            </a>
                        </div>
                    `;
                    return;
                }
                
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkAnalysis, 1000);
                } else {
                    content.innerHTML = `
                        <h2>⏰ Анализ занимает больше времени</h2>
                        <p>Анализ все еще выполняется. Вы можете проверить результат позже в истории тренировок.</p>
                        <div style="margin-top: 20px; text-align: center;">
                            <button onclick="document.getElementById('analysisModal').style.display='none'" class="btn btn-secondary">
                                Закрыть
                            </button>
                        </div>
                    `;
                }
                
            } catch (error) {
                console.error('Ошибка проверки анализа:', error);
                content.innerHTML = `
                    <h2>❌ Ошибка анализа</h2>
                    <p>Не удалось проанализировать тренировку. Попробуйте позже.</p>
                    <div style="margin-top: 20px; text-align: center;">
                        <button onclick="document.getElementById('analysisModal').style.display='none'" class="btn btn-secondary">
                            Закрыть
                        </button>
                    </div>
                `;
            }
        };

        setTimeout(checkAnalysis, 2000); // Начинаем проверку через 2 секунды
    }
}

// Инициализируем приложение при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new SalesTrainingApp();
});