# PSG Connect FastAPI Backend



This project is a backend service built with FastAPI that provides web scraping functionality for PSG Connect. It offers a RESTful API for clients to fetch student data from the PSG Tech website.

## Features

- Web scraping API endpoint
- Student profile, attendance, exam results, and CA marks retrieval
- Error handling for various scenarios
- CORS middleware for cross-origin requests

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn (ASGI server)
- Pydantic
- Custom scraping module (`dataFetchFunctions`)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/psg-connect-backend.git
   cd psg-connect-backend
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the FastAPI server:

```
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## API Endpoints

- `GET /`: Welcome message
- `GET /online`: Check if the service is online
- `POST /fetch_data`: Fetch student data (requires username and password)

## Code Structure

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dataFetchFunctions import CAMarksWebScrapper
from dataExceptions import InvalidUsernameOrPasswordException, ScrappingError, NoSemResultsAvailable, NoCAMarksAvailable, AttendanceUpdateInProcessException, NoTimeTableDataException

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Credentials(BaseModel):
    username: str
    password: str

# API endpoints implementation
# ...
```

## Deployment

This project is designed to be deployed using a Heroku-style Procfile. Make sure to configure your deployment environment accordingly.

## Error Handling

The backend handles various exceptions:

- Invalid username or password
- Scraping errors
- No semester results available
- No CA marks available
- Attendance update in process
- No timetable data available

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/my-new-feature`
5. Submit a pull request
