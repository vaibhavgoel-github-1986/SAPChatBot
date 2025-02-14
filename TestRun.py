import time

from ChatModels.GetAuthToken import clear_auth_token, get_auth_token

# Get the start time as a floating-point timestamp
start_time = time.time()


# Get Token
clear_auth_token()
token = get_auth_token()
print(token)
print()

# Sleep for 3 seconds (Example Delay)
sleep_time = 3
time.sleep(sleep_time)

# Get the current time
token = get_auth_token()
print(token)
