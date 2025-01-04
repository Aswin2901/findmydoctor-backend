from datetime import datetime, timedelta, time

def generate_time_slots(start_time, end_time, duration):
    slots = []
    
    # Convert the start and end times to datetime objects by adding a date
    start_datetime = datetime.combine(datetime.today(), start_time)
    end_datetime = datetime.combine(datetime.today(), end_time)
    
    current_time = start_datetime
    
    while current_time + timedelta(minutes=duration) <= end_datetime:
        # Add the formatted time to the slots list
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=duration)
    
    return slots

def is_time_in_range(start, end, check):
    """Check if a given time is within a specific range."""
    return start <= check < end
