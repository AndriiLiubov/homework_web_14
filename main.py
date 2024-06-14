import os
from dotenv import load_dotenv

from fastapi import FastAPI
from src.routes import contacts, auth, users
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_host = os.environ.get('REDIS_DOMAIN')
redis_port = int(os.environ.get('REDIS_PORT'))


app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.on_event("startup")
async def startup():
    """
    Initialize Redis connection and FastAPILimiter on application startup.

    This function sets up the Redis connection and initializes the FastAPILimiter with Redis for rate limiting.

    :return: None
    """
    r = await redis.Redis(host=redis_host, port=redis_port, db=0, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)

@app.get("/")
def read_root():
    """
    Root endpoint of the application.

    This endpoint returns a welcome message indicating the application is a contacts app.

    :return: dict: A dictionary containing a welcome message
    """
    return {"Welcome to contacts app"}