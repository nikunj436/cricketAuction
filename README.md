# Cricket Auction API

This is the backend API for a cricket auction application, built with FastAPI and SQLAlchemy.

---

## Setup and Installation

### Prerequisites
- Python 3.11 or higher
- A running PostgreSQL database

---

### Steps

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd cricket-auction-fastapi
    ```

2.  **Create and Activate Virtual Environment**
    It is highly recommended to use a virtual environment to manage project dependencies.

    * **Create the environment (using Python 3.11):**
        ```sh
        python3.11 -m venv venv
        ```

    * **Activate the environment:**
        ```sh
        source venv/bin/activate
        ```
        Your terminal prompt should now start with `(venv)`.

3.  **Install Dependencies**
    Install all required packages from the `requirements.txt` file.
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory by copying the example.
    ```sh
    cp .env.example .env
    ```
    Now, edit the `.env` file with your database credentials and a unique secret key.
    ```env
    DATABASE_URL="postgresql://user:password@host:port/dbname"
    SECRET_KEY="<your_super_secret_random_string_here>"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_DAYS=7
    ```

---

## How to Run the Application

With the virtual environment activated, run the Uvicorn server from the root directory:

```sh
uvicorn app.main:app --reload
```
The `--reload` flag automatically restarts the server when you make code changes.

The API will be available at `http://127.0.0.1:8000`.

---

## API Documentation

Once the server is running, you can access the interactive API documentation (Swagger UI) at:

[**http://127.0.0.1:8000/docs**](http://127.0.0.1:8000/docs)