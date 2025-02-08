import time

# Get the start time as a floating-point timestamp
start_time = time.time()

# Sleep for 3 seconds (Example Delay)
sleep_time = 3
time.sleep(sleep_time)

# Get the current time
current_time = time.time()  # Keep as float for accuracy

# Check if the difference is >= 5 seconds
if (current_time - start_time) >= 3:
    print("✅ More than 5 seconds have passed.")
else:
    print("⏳ Less than 5 seconds have passed.")
