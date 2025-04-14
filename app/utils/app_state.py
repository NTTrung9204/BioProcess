import datetime

# Global application state
producer_running = True
active_streams = {}
server_start_time = datetime.datetime.now()

def get_producer_running():
    global producer_running
    return producer_running

def set_producer_running(status):
    global producer_running
    producer_running = status
    return producer_running

def get_server_start_time():
    global server_start_time
    return server_start_time

def get_server_uptime():
    uptime = datetime.datetime.now() - server_start_time
    uptime_seconds = uptime.total_seconds()
    
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        'days': int(days),
        'hours': int(hours),
        'minutes': int(minutes),
        'seconds': int(seconds)
    }

def get_active_streams():
    global active_streams
    return active_streams

def add_active_stream(stream_id, stream_data):
    global active_streams
    active_streams[stream_id] = stream_data
    return active_streams

def remove_active_stream(stream_id):
    global active_streams
    if stream_id in active_streams:
        del active_streams[stream_id]
    return active_streams 