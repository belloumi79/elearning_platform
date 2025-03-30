from dotenv import load_dotenv
load_dotenv()  # This should load environment variables from .env file

from app import create_app
from config.logging_config import init_logging

init_logging()
app = create_app()

# Log startup message
app.logger.info('E-learning platform application started')

# Log startup message
app.logger.info('E-learning platform application started')

if __name__ == '__main__':
    app.run(debug=True)
