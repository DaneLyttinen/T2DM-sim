import numpy as np

def time_to_minutes(hour_minute):
    """Converts a time given in (hour, minute) format to minutes since midnight."""
    hour, minute = hour_minute
    return hour * 60 + minute

def TrapezoidFunc(c, t1, t2, t3, t4):
    # Convert timepoints to minutes since midnight
    t1_minutes = time_to_minutes(t1)
    t2_minutes = time_to_minutes(t2)
    t3_minutes = time_to_minutes(t3)
    t4_minutes = time_to_minutes(t4)
    time_intervals = np.arange(t1_minutes, t4_minutes+5, 5)
    function_values_intervals = []

    for t in time_intervals:
        if t < t2_minutes:
            value = (c / (t2_minutes - t1_minutes)) * (t - t1_minutes)
        elif t2_minutes <= t <= t3_minutes:
            value = c
        elif t > t3_minutes:
            value = c - (c / (t4_minutes - t3_minutes)) * (t - t3_minutes)
        function_values_intervals.append(value)
    print(function_values_intervals)
    return function_values_intervals
