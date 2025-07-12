# Alpaca Trading Bot

A Python-based trading bot that uses the Alpaca API to execute trades based on a defined strategy. It scrapes Yahoo Finance for potential opportunities among stocks and cryptocurrencies, analyzes them using technical indicators, and makes trading decisions.

---

## 📁 Project Structure

```
/your-project-folder
|-- main.py              # Main script to run the bot
|-- requirements.txt
|-- .env.example
|-- README.md
|-- src/
|   |-- __init__.py      # Makes 'src' a Python package
|   |-- config.py
|   |-- data_fetcher.py
|   |-- notifications.py
|   |-- strategy.py
|   |-- trader.py
```

- **main.py**: The main entry point for the application. Initializes all components and starts the trading process.
- **src/**: Main source package containing all the bot's logic.
    - **config.py**: Manages all configuration settings, loading them from a `.env` file.
    - **data_fetcher.py**: Scrapes Yahoo Finance and enriches assets with technical indicators.
    - **trader.py**: Handles all interactions with the Alpaca API.
    - **strategy.py**: Defines the logic for making trading decisions.
    - **notifications.py**: Handles sending updates to Telegram.
- **requirements.txt**: List of all Python packages required.
- **.env.example**: Example file showing the required environment variables.

---

## 🚀 How to Run

### 1. Clone or Download

Place all the files in a project folder, maintaining the structure shown above.

### 2. Install Dependencies

Make sure you have Python 3 installed. Then, install the required packages from the project's root directory:

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

- Rename the `.env.example` file to `.env`.
- Open the `.env` file and fill in your Alpaca API keys and Telegram bot details.

### 4. Run the Bot

Execute the `main.py` script from your terminal in the project's root directory:

```bash
python main.py
```

The bot will then perform a single run: find opportunities, analyze them, and attempt to place trades based on the strategy.

---