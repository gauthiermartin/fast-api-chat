# FastAPI Chat

A real-time chat application built with FastAPI and WebSockets.

## Description

This project is a modern chat application that leverages FastAPI's high-performance framework to provide real-time messaging capabilities through WebSocket connections.

## Features (Planned)

- Real-time messaging with WebSockets
- Multiple chat rooms
- User authentication
- Message history
- Modern web interface
- RESTful API endpoints

## Tech Stack

- **Backend**: FastAPI
- **WebSockets**: For real-time communication
- **Database**: TBD (PostgreSQL/SQLite)
- **Frontend**: TBD (React/Vue.js/vanilla JS)

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fast-api-chat.git
   cd fast-api-chat
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
fast-api-chat/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   ├── routers/
│   └── websocket/
├── static/
├── templates/
├── requirements.txt
├── .gitignore
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/fast-api-chat](https://github.com/yourusername/fast-api-chat)
