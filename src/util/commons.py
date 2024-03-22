

# datetime to timestamp

def datetime_to_epoch(value):
    if value:
        return int(value.timestamp() * 1000)
    else:
        return value

















