import sys
from flask import abort
import pymysql
from dbutils.pooled_db import PooledDB
from config import OPENAPI_STUB_DIR, DB_HOST, DB_USER, DB_PASSWD, DB_NAME

sys.path.append(OPENAPI_STUB_DIR)
from swagger_server import models

pool = PooledDB(creator=pymysql,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWD,
                database=DB_NAME,
                maxconnections=1,
                blocking=True)

def get_sensor_room_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, temp, hum
            FROM sensorRoomData
        """)
        result = [models.SensorRoomData(*row) for row in cs.fetchall()]
        return result
    
def get_sensor_tank_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, temp, hum
            FROM sensorTankData
        """)
        result = [models.SensorTankData(*row) for row in cs.fetchall()]
        return result
    
def get_behavior_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, status, freq
            FROM behaviorData
        """)
        result = [models.BehaviorData(*row) for row in cs.fetchall()]
        return result
    
def get_feeding_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, dis, por
            FROM feedingData
        """)
        result = [models.FeedingData(*row) for row in cs.fetchall()]
        return result

def get_feeding_details(id):
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, dis, por
            FROM feedingData
            WHERE id=%s
            """, [id])
        result = cs.fetchone()
    if result:
        return models.FeedingData(*result)
    else:
        abort(404)
