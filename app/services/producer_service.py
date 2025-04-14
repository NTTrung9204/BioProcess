import json
import time
import pandas as pd
import requests
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from app.config import KafkaConfig, PostgresConfig, HostConfig, UserConfig, PathConfig
from app.repositories import fetch_data, insert_data_to_db
from app.utils import (
    load_plsr_model,
    load_scaler,
    load_ml_model,
    map_record,
    predict_raman,
    predict_ml_model,
    get_producer_running
)

def produce_data():
    print(f"🔄 Connecting to Kafka broker: {KafkaConfig.KAFKA_BROKER}", flush=True)
    
    # Thử kết nối đến Kafka broker với cơ chế retry
    max_retries = 10
    retry_delay = 5  # seconds
    producer = None
    
    for attempt in range(1, max_retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KafkaConfig.KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                # Thêm các tham số timeout để phát hiện lỗi kết nối nhanh hơn
                request_timeout_ms=5000,   # 5 seconds
                connections_max_idle_ms=30000, # 30 seconds
                max_block_ms=10000,  # 10 seconds
                # Thử kết nối nhiều lần trong KafkaProducer
                reconnect_backoff_ms=1000,  # 1 second
                reconnect_backoff_max_ms=10000,  # 10 seconds
            )
            print(f"✅ Connected to Kafka broker after {attempt} attempt(s)", flush=True)
            break
        except Exception as e:
            print(f"❌ Attempt {attempt}/{max_retries} failed: {str(e)}", flush=True)
            if attempt == max_retries:
                print(f"❌ Failed to connect to Kafka broker after {max_retries} attempts", flush=True)
                # Sleep and then try again (outer loop will handle reconnection)
                time.sleep(60)
                return produce_data()  # Recursive call to try again
            time.sleep(retry_delay)
    
    if not producer:
        print("❌ Could not establish connection to Kafka. Retrying in 1 minute...", flush=True)
        time.sleep(60)
        return produce_data()  # Recursive call to try again
    
    print(f"✅ Producer running successfully", flush=True)

    scan = 0
    while True:
        try:
            records = fetch_data()
            if not records:
                print("No data in the database!", flush=True)
                time.sleep(5)
                continue

            for record in records:
                if not get_producer_running():
                    print("Producer paused...", flush=True)
                    time.sleep(5)
                    continue

                try:
                    mapped_record = record
                    # mapped_record = map_record(record)
                    mapped_record[PostgresConfig.TIMESTAMP] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    mapped_record[PostgresConfig.SCAN] = scan
                    mapped_record[UserConfig.ADMIN_USERNAME] = UserConfig.ADMIN_PASSWORD
                    
                    # Thêm timeout để tránh blocking quá lâu
                    send_future = producer.send(KafkaConfig.KAFKA_TOPIC_PILOT, value=mapped_record)
                    # Đợi kết quả gửi message với timeout
                    send_future.get(timeout=5)

                    print(
                        f"Produced Operation: {record['timestamp']} | Scan: {scan}", flush=True
                    )

                    scan += 1
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ Error sending message: {str(e)}", flush=True)
                    # Nếu lỗi xảy ra khi gửi message, thử kết nối lại
                    if "KafkaTimeoutError" in str(e) or "NoBrokersAvailable" in str(e):
                        print("❌ Kafka connection issue. Attempting to reconnect...", flush=True)
                        return produce_data()  # Restart the producer
                    time.sleep(5)  # Đợi một chút trước khi thử lại với record tiếp theo
        except Exception as e:
            print(f"❌ Error in producer main loop: {str(e)}", flush=True)
            print("Restarting producer in 10 seconds...", flush=True)
            time.sleep(10)
            return produce_data()  # Restart the producer

def stream_data_to_another_VM(data):
    KAFKA_TOPIC = KafkaConfig.KAFKA_TOPIC_PILOT
    KAFKA_REST_URL = f"http://{HostConfig.HOST_TARGET}/kafka-rest"
    headers = {
        'Content-Type': 'application/vnd.kafka.json.v2+json'
    }

    payload = {
        "records": [
            {
                "value": data
            }
        ]
    }

    response = requests.post(
        f"{KAFKA_REST_URL}/topics/{KAFKA_TOPIC}",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        print(f"Produced Operation: {data['timestamp']}", flush=True)
    else:
        print(f"Error producing message: {response.text}", flush=True)

def consume_kafka():
    print("🔄 Kafka consumer starting...", flush=True)
    
    # Thử kết nối Consumer với cơ chế retry
    max_retries = 10
    retry_delay = 5  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries} to initialize Kafka consumer...", flush=True)
            print(f"Kafka broker: {KafkaConfig.KAFKA_BROKER}", flush=True)
            print(f"Kafka topics: {KafkaConfig.TOPICS}", flush=True)
            
            # Thử tạo consumer với các tham số timeout phù hợp
            consumer = KafkaConsumer(
                *KafkaConfig.TOPICS,
                bootstrap_servers=KafkaConfig.KAFKA_BROKER,
                auto_offset_reset="earliest",
                group_id="sensor_group",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                # Thêm các tham số timeout
                session_timeout_ms=30000,  # 30 seconds
                request_timeout_ms=40000,  # 40 seconds
                # Cấu hình thử kết nối lại
                reconnect_backoff_ms=1000,  # 1 second
                reconnect_backoff_max_ms=10000,  # 10 seconds
                # Cấu hình heartbeat
                heartbeat_interval_ms=3000,  # 3 seconds
            )
            
            print("✅ Kafka consumer successfully connected", flush=True)
            break
        except Exception as e:
            print(f"❌ Consumer initialization attempt {attempt} failed: {str(e)}", flush=True)
            if attempt == max_retries:
                print(f"❌ Failed to initialize Kafka consumer after {max_retries} attempts. Retrying in 60 seconds...", flush=True)
                time.sleep(60)
                return consume_kafka()  # Recursive call to try again
            time.sleep(retry_delay)
    
    try:
        print("🔍 Loading models...", flush=True)
        # Load các models cần thiết
        ml_model = load_ml_model()
        print("✅ ML model loaded successfully", flush=True)
        plsr_model = load_plsr_model()
        print("✅ PLSR model loaded successfully", flush=True)

        scaler_x = load_scaler(PathConfig.MODEL_2_SCALER_X)
        print("✅ Scaler X loaded successfully", flush=True)
        scaler_y = load_scaler(PathConfig.MODEL_2_SCALER_Y)
        print("✅ Scaler Y loaded successfully", flush=True)
        
        print("🔄 Starting consumer loop - waiting for messages...", flush=True)
        
        # Vòng lặp chính để xử lý message
        while True:
            try:
                # Thiết lập timeout để lấy message
                message_batch = consumer.poll(timeout_ms=5000)
                
                if not message_batch:
                    # Không có message mới, tiếp tục lặp
                    continue
                
                # Xử lý các message nhận được
                for tp, messages in message_batch.items():
                    for message in messages:
                        try:
                            data = message.value
                            
                            if UserConfig.ADMIN_USERNAME not in data or data[UserConfig.ADMIN_USERNAME] != UserConfig.ADMIN_PASSWORD:
                                print("Insufficient permissions to stream data!", flush=True)
                                continue

                            if HostConfig.HOST_TARGET:
                                stream_data_to_another_VM(data)

                            del data[UserConfig.ADMIN_USERNAME]

                            if PostgresConfig.SCAN not in data or data[PostgresConfig.SCAN] is None:
                                data[PostgresConfig.SCAN] = "empty_scan"

                            if message.topic == KafkaConfig.KAFKA_TOPIC_PILOT:
                                data[PostgresConfig.PREDICTED_OIL] = predict_ml_model(data, ml_model)[0][0]
                                insert_data_to_db(
                                    PostgresConfig.TABLE_NAME_PILOT, data, ml_model
                                )
                            elif message.topic == KafkaConfig.KAFKA_TOPIC_FTIR:
                                df = pd.DataFrame(data, index=[0])
                                data[PostgresConfig.PREDICTED_OIL_CONCENTRATION] = predict_raman(df, plsr_model)[0][0]

                                insert_data_to_db(
                                    PostgresConfig.TABLE_NAME_FTIR,
                                    data,
                                    plsr_model,
                                    scaler_x,
                                    scaler_y,
                                )

                            print(
                                f"📥 Received {data[PostgresConfig.TIMESTAMP]} from {message.topic}",
                                flush=True,
                            )
                        except Exception as e:
                            print(f"❌ Error processing message: {str(e)}", flush=True)
                            # Tiếp tục với message tiếp theo
                            continue
                
                # Commit offset sau khi xử lý xong batch
                consumer.commit()
                
            except Exception as e:
                if "NoBrokersAvailable" in str(e) or "KafkaTimeoutError" in str(e) or "NodeNotReadyError" in str(e):
                    print(f"❌ Kafka connection error: {str(e)}", flush=True)
                    print("🔄 Attempting to reconnect consumer...", flush=True)
                    time.sleep(10)
                    return consume_kafka()  # Khởi động lại consumer
                else:
                    print(f"❌ Unexpected error in consumer loop: {str(e)}", flush=True)
                    time.sleep(5)  # Đợi một chút và tiếp tục
        
    except Exception as e:
        print(f"❌ Kafka consumer fatal error: {e}", flush=True)
        print("🔄 Restarting consumer in 30 seconds...", flush=True)
        time.sleep(30)
        return consume_kafka()  # Khởi động lại consumer 