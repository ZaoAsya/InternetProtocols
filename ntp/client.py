import ntplib
import time

while True:        
    client = ntplib.NTPClient()
    request = client.request('127.0.0.1')
    time_ntp = int(request.tx_time)
    time_system = int(time.time())
    print ("Time difference " + str(time_ntp - time_system))

    time.sleep(1)
    
