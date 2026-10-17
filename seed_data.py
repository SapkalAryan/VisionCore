import csv
import random
from datetime import datetime, timedelta

# Generate 24 hours of realistic data
start_time = datetime.now() - timedelta(days=1)
start_time = start_time.replace(hour=0, minute=0, second=0)

with open("data/occupancy_log.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "person_count", "hour", "weekday", "occupied", "lights_on", "brightness"])
    
    for i in range(24 * 60): # Every minute for 24 hours
        current_time = start_time + timedelta(minutes=i)
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # Simulate typical lab usage: Empty at night, busy during day
        if 8 <= hour <= 18:
            person_count = random.choice([0, 1, 2, 3, 4])
            if random.random() < 0.2: person_count = 0 # occasionally empty
        else:
            person_count = 0 # Empty at night
            
        occupied = 1 if person_count > 0 else 0
        lights_on = 1 if 7 <= hour <= 19 else 0
        brightness = random.randint(100, 150) if lights_on else random.randint(20, 50)
        
        writer.writerow([
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            person_count, hour, weekday, occupied, lights_on, brightness
        ])

print("Seeded 1440 rows of realistic data!")