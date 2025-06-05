# CherryGPT – локальный чат-бот на Ollama + LangChain + Chainlit

CherryGPT — это офлайн-решение для разговорного ИИ, которое:

* **Работает полностью локально** – LLM разворачивается через [Ollama](https://ollama.ai)  
* **Использует LangChain** как backend-оркестратор (memory, промпты, runnable-граф)  
* **Показывает интерфейс на Chainlit** – лёгкий web-UI, out-of-the-box hot-reload  
* **Логирует вызовы в Literal** (если указать ключи)  
* Поддерживает ***мгновенный перевод сообщений*** через `deep-translator`  
* Локализован: en | ru | kz (см. `.chainlit/translations/*`)

## ⚙️ Быстрый старт

```bash
# 1. Клонируем репозиторий и заходим в папку
git clone https://github.com/yuzaarissha/CherryGPT.git
cd cherrygpt

# 2. Создаём и активируем виртуальное окружение
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# 3. Ставим зависимости
pip install -r requirements.txt

# 4. Ставим и запускаем Ollama (см. https://ollama.ai/download)
ollama pull llama3        # или любую другую модель
ollama serve &            # запустить сервер в фоне

# 5. (Необязательно) задаём переменные окружения
cp .env.example .env      # и заполнить по желанию

# 6. Запускаем UI
chainlit run app.py -w    # -w = live-reload
