import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np

def read_sensor_data_to_df(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r' - ', line)
            entry = {}
            for part in parts:
                kv_match = re.match(r'([^:]+):\s*(.+)', part)
                if kv_match:
                    key = kv_match.group(1).strip()
                    value = kv_match.group(2).strip()
                    entry[key] = value

            if 'Temp' in entry:
                entry['Temp'] = float(entry['Temp'][:-3])
            if 'Humidity' in entry:
                entry['Humidity'] = float(entry['Humidity'][:-1])
            if 'CO2' in entry:
                entry['CO2'] = float(entry['CO2'][:-4])
            for pm_field in ['PM1', 'PM2.5', 'PM10']:
                if pm_field in entry:
                    entry[pm_field] = float(entry[pm_field])

            if 'Datetime' in entry:
                raw_dt = entry['Datetime']
                try:
                    raw_time = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M:%S.%f")
                    entry['Datetime'] = raw_time.isoformat()
                except Exception as e:
                    print(f"Datetime parse error: {e}")

            data.append(entry)
    df = pd.DataFrame(data)
    return df

def sensor_at(ts: datetime, sensor_times):
    """Return the *latest* sensor row ≤ ts or None if ts is earlier."""
    idx = sensor_times.searchsorted(np.datetime64(ts), side="right") - 1
    if idx < 0:
        return None
    return idx

