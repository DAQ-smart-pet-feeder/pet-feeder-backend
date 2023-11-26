import sys
from flask import abort, request
import pymysql
import json
from dbutils.pooled_db import PooledDB
from config import OPENAPI_STUB_DIR, DB_HOST, DB_USER, DB_PASSWD, DB_NAME

sys.path.append(OPENAPI_STUB_DIR)
from swagger_server import models
import paho.mqtt.client as mqtt
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# MQTT Parameters
MQTT_BROKER = "iot.cpe.ku.ac.th"
MQTT_USER = "b6410546203"
MQTT_PASS = "preawpan.t@ku.th"

# Initialize client
client = mqtt.Client(client_id="")  # use a unique client ID

# Set credentials
client.username_pw_set(MQTT_USER, MQTT_PASS)

# Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully.")
    else:
        print(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    print("Disconnected")

client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Connect
try:
    client.connect(MQTT_BROKER, 1883, 60)  # You can specify the port if it's not the default
except Exception as e:
    print(f"Error connecting to MQTT Broker: {e}")

pool = PooledDB(creator=pymysql,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWD,
                database=DB_NAME,
                maxconnections=2,
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

def get_tank_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT remaining_percentage, feeding_status
            FROM tankData
            ORDER BY id DESC
            LIMIT 1
        """)
        result = [{'remaining_percentage': int(row[0]), 'feeding_status': int(row[1])} for row in cs.fetchall()]
        return result

   
def get_feeding_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT id, ts, por
            FROM feedingData
        """)
        result = [models.FeedingData(*row) for row in cs.fetchall()]
        return result


def get_behavior_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT status, ts
            FROM behaviorData
        """)
        result = [{'stat': int(row[0]), 'ts': str(row[1])} for row in cs.fetchall()]
        return result


def get_meal_plan_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT schedule_id, days, por, time, enable_status
            FROM mealPlan
        """)
        data_list = [{'schedule_id': int(row[0]),
                      'day': eval(row[1]),  # Using eval to convert the string to a list
                      'por': int(row[2]),
                      'time': str(row[3]),
                      'enable_status': int(row[4])} for row in cs.fetchall()]
        if not data_list:
            return None
        return data_list

def post_portion_data():
    try:
        with pool.connection() as conn, conn.cursor() as cs:
            request_data = request.get_json() 
        # Example: Insert data into a 'feedingData'
            insert_query = "INSERT INTO feedingData (por) VALUES (%s)"
            cs.execute(insert_query, (request_data['por']))

        # Commit changes and close the database connection
            conn.commit()
        # Return success message or relevant data
        client.publish('daq2023/group4/quick_meal', request_data['por'])
        return {'message': 'Data inserted successfully'}, 201

    except Exception as e:
        # Handle errors appropriately
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500

def post_tank_data():
    try:
        with pool.connection() as conn, conn.cursor() as cs:
            request_data = request.get_json() 
            print(request_data)
            insert_query = "INSERT INTO tankData (remaining_percentage, feeding_status) VALUES (%s, %s)"
            cs.execute(insert_query, (request_data['remaining_percentage'], request_data['feeding_status']))

            # Commit changes and close the database connection
            conn.commit()

            # Return success message or relevant data
            return {'message': 'Data inserted successfully'}, 201

    except Exception as e:
        # Handle errors appropriately
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500

def post_meal_plan_data():
    try:
        with pool.connection() as conn, conn.cursor() as cs:

            input_data = request.get_json() 
            print(1)
            transformed_data = []

            # Check if schedule_id already exists in the database
            check_query = "SELECT * FROM mealPlan WHERE schedule_id = %s"
            cs.execute(check_query, (input_data['schedule_id'],))
            existing_record = cs.fetchone()

            if existing_record:
                # Update enable_status if schedule_id already exists
                update_query = "UPDATE mealPlan SET enable_status = %s WHERE schedule_id = %s"
                cs.execute(update_query, (input_data['enable_status'], input_data['schedule_id']))
            else:
                # Insert new records if schedule_id doesn't exist
                insert_query = "INSERT INTO mealPlan (schedule_id, days, por, time, enable_status) VALUES (%s, %s, %s, %s, %s)"

                transformed_entry = {
                        'schedule_id': input_data['schedule_id'],
                        'days': str(input_data['days']),
                        'por': input_data['por'],
                        'time': input_data['time'],
                        'enable_status': input_data['enable_status']
                    }
                transformed_data.append(transformed_entry)
                print(2)
                # Execute the query for each transformed entry
                for transformed_entry in transformed_data:
                    cs.execute(insert_query, (transformed_entry['schedule_id'], transformed_entry['days'], transformed_entry['por'], transformed_entry['time'], transformed_entry['enable_status']))
            # Commit changes after all queries have been executed
            conn.commit()
            meal_plan = json.dumps(get_meal_plan_data())
            client.publish('daq2023/group4/meal_plan', meal_plan)

            # Return success message or relevant data
            return {'message': 'Data inserted or updated successfully'}, 201

    except Exception as e:
        # Handle errors appropriately
        print(f"Error: {e}")
        return {'error': 'Internal Server Error'}, 500


def get_room_tank_env_data():
    room_data = get_sensor_room_data()
    tank_data = get_sensor_tank_data()
    env_data = get_env_data()
    return [models.RoomTankEnvData(room_data[1], room_data[2], room_data[3], tank_data[1], tank_data[2], env_data[1], env_data[2], env_data[3])]


def get_sensor_room_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, temp, hum, pm FROM sensorRoomData
            ORDER BY id DESC LIMIT 1
        """)
        result = [row for row in cs.fetchall()]
        return result[0]


def get_sensor_tank_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, temp, hum FROM sensorTankData
            ORDER BY id DESC LIMIT 1
        """)
        result = [row for row in cs.fetchall()]
        return result[0]


def get_env_data():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT ts, temp, hum, pm FROM envData
            ORDER BY id DESC LIMIT 1
        """)
        result = [row for row in cs.fetchall()]
        return result[0]


def get_room_data_for_visualization():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT DATE(ts), AVG(hum) AS hum_avg, MIN(temp) AS temp_min, 
            MAX(temp) AS temp_max, MIN(pm) AS pm_min, MAX(pm) AS pm_max 
            FROM sensorRoomData
            WHERE DATE(ts) BETWEEN CURRENT_DATE() - INTERVAL 7 DAY AND CURRENT_DATE()
            GROUP BY DATE(ts)
        """)
        result = [{
            "date": row[0],
            "hum_avg": row[1],
            "temp_min": row[2],
            "temp_max": row[3],
            "pm_min": row[4],
            "pm_max": row[5]
        } for row in cs.fetchall()]
        return result if result else None


def get_tank_data_for_visualization():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT DATE(ts), AVG(hum), MIN(temp) AS temp_min, MAX(temp) AS temp_max
            FROM sensorTankData
            WHERE DATE(ts) BETWEEN CURRENT_DATE() - INTERVAL 7 DAY AND CURRENT_DATE()
            GROUP BY DATE(ts)
        """)
        result = [
            {
                "date": row[0],
                "hum_avg": row[1],
                "temp_min": row[2],
                "temp_max": row[3],
            }
            for row in cs.fetchall()
        ]
        return result if result else None


def get_pm25_and_eating_time():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT pm25, GROUP_CONCAT(eating_time ORDER BY eating_time)
            FROM dataVisual
            GROUP BY pm25
        """)
        result = [
            {
                "pm25": row[0],
                "eating_time": eval(row[1])
            }
            for row in cs.fetchall()
        ]
        return result if result else None


def get_temp_and_eating_time():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT temp, GROUP_CONCAT(eating_time ORDER BY eating_time)
            FROM dataVisual
            GROUP BY temp
        """)
        result = [
            {
                "temp": row[0],
                "eating_time": eval(row[1])
            }
            for row in cs.fetchall()
        ]
        return result if result else None


def get_hum_and_eating_time():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT hum, GROUP_CONCAT(eating_time ORDER BY eating_time)
            FROM dataVisual
            GROUP BY hum
        """)
        result = [
            {
                "hum": row[0],
                "eating_time": eval(row[1])
            }
            for row in cs.fetchall()
        ]
        return result if result else None
