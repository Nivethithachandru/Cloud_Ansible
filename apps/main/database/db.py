from sqlalchemy import create_engine
from apps.main.config import *
import os
import asyncpg
from fastapi import FastAPI, Depends
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import urlparse

hostdb_engine = None
hostdb_SessionLocal = None


Base = declarative_base()

SPLIT_HOSTDB_URL = urlparse(HOSTDB_URL)
HOSTDB_DATABASE_NAME = SPLIT_HOSTDB_URL.path[1:]  


async def hostpc_db_create():
    conn = await asyncpg.connect(user= SPLIT_HOSTDB_URL.username, 
                                 password=SPLIT_HOSTDB_URL.password, 
                                 database="postgres", host=SPLIT_HOSTDB_URL.hostname)
    db_exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{HOSTDB_DATABASE_NAME}';")    
    if not db_exists:
        await conn.execute(f'CREATE DATABASE "{HOSTDB_DATABASE_NAME}";')
        print(f"Database '{HOSTDB_DATABASE_NAME}' created.")
    else:
        print(f"Database '{HOSTDB_DATABASE_NAME}' already exists.")
    await conn.close()


async def initialize_database():
    global hostdb_engine, hostdb_SessionLocal
    
    await hostpc_db_create()
  
    # Initialize the HOST database connection
    hostdb_engine = create_engine(HOSTDB_URL, pool_size=150, max_overflow=80, pool_timeout=60, pool_recycle=3600)
    
    
    hostdb_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=hostdb_engine)
    Base.metadata.create_all(bind=hostdb_engine) 

    
def get_db():  
    if hostdb_SessionLocal is None:
        raise Exception("Database session local is not initialized.")
    db = hostdb_SessionLocal()  
    try:
        yield db
    finally:
        db.close()  


app = FastAPI()

@app.on_event("startup")
async def app_startup():
    await initialize_database()  