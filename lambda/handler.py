import json
import math
import boto3
from datetime import datetime

SNS_TOPIC = 'arn:aws:sns:us-east-1:202945989660:Publish_temp_info'

sns_client = boto3.client("sns")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("SensorFailuresTF")

def mark_sensor_as_broken(sensor_id):
    table.put_item(
        Item={
            "sensor_id": int(sensor_id),
            "broken": True,
            "timestamp": datetime.now().isoformat()
        }
    )

def lambda_handler(event, context):
    a = 1.4e-3
    b = 2.37e-4
    c = 9.9e-8

    if not isinstance(event, list):
        return {
            "statusCode": 400,
            "error": "INVALID_INPUT_FORMAT",
            "message": "Expected a list of sensor readings."
        }

    results = []

    for reading in event:
        try:
            if "sensor_id" not in reading or "value" not in reading or "location_id" not in reading:
                continue

            sensor_id = reading["sensor_id"]
            resistance = reading["value"]
            location_id = reading["location_id"]

            if not isinstance(sensor_id, (int, str)) or not str(sensor_id).isdigit():
                continue

            try:
                resistance = float(resistance)
            except ValueError:
                mark_sensor_as_broken(sensor_id)
                results.append({"sensor_id": sensor_id, "status": "BROKEN", "code": 422})
                continue

            if resistance < 1 or resistance > 20000:
                mark_sensor_as_broken(sensor_id)
                results.append({"sensor_id": sensor_id, "status": "RESISTANCE_OUT_OF_RANGE", "code": 422})
                continue

            temperature = round(1 / (a + b * math.log(resistance) + c * pow(math.log(resistance), 3)) - 273, 2)

            if temperature < -273.15:
                status = "INVALID_TEMPERATURE"
                code = 500
            elif temperature < 20:
                status = "TEMPERATURE_TOO_LOW"
                code = 206
            elif temperature > 100 and temperature < 250:
                status = "TEMPERATURE_TOO_HIGH"
                code = 206
            elif temperature >= 250:
                status = "TEMPERATURE_CRITICAL"
                code = 500
                message = (
                    f"Dear sir,\n\n"
                    f"The temperature on sensor ID:{sensor_id} has reached a critical value of *{temperature} °C*!\n"
                    f"You have to react fast and disable the machine!\n\n"
                    f"Best regards,\nlambda function"
                )
                subject = f"CRITICAL TEMPERATURE ON SENSOR: {sensor_id}!"
                sns_client.publish(
                    TopicArn=SNS_TOPIC,
                    Message=message,
                    Subject=subject
                )
            else:
                status = "OK"
                code = 200

            timestamp_formatted = datetime.now().strftime("%d/%m/%y %H:%M")

            results.append({
                "sensor_id": sensor_id,
                "temperature": temperature,
                "location_id": location_id,
                "timestamp": timestamp_formatted,
                "status": status,
                "code": code
            })

        except Exception as e:
            results.append({
                "sensor_id": reading.get("sensor_id"),
                "status": "ERROR",
                "error": str(e),
                "code": 500
            })

    return {
        "statusCode": 207 if any(r["code"] != 200 for r in results) else 200,
        "results": results
    }
