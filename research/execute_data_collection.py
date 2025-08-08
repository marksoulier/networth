import time

def data_collection():
    # Placeholder for actual data collection logic
    print("Collecting data...")

if __name__ == "__main__":
    while True:
        start_time = time.time()
        data_collection()
        elapsed = time.time() - start_time
        sleep_time = 60 - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
        # If elapsed >= 60, immediately start next iteration 
