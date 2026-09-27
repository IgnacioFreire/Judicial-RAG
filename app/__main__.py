"""Run the API and the built React UI on port 8501."""

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8501)
