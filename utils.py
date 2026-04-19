def deep_merge(master, new_data):
    for key, value in new_data.items():
        if value is None:
            continue

        if key in master:
            if isinstance(value, list) and isinstance(master[key], list):
                master[key] = list({item: None for item in (master[key] + value)}.keys())
            elif isinstance(value, dict) and isinstance(master[key], dict):
                deep_merge(master[key], value)
            else:
                master[key] = value
        else:
            master[key] = value
