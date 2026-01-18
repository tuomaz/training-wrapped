import pandas as pd
import os
import re
import glob
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P

def get_cell_text(cell):
    text_elements = []
    for element in cell.childNodes:
        if element.qname[1] == 'p':
            for text in element.childNodes:
                if text.nodeType == 3: # Text node
                    text_elements.append(str(text))
    return "".join(text_elements)

def parse_ods_cycling(filepath):
    print(f"--- Parsing Cycling Data from {filepath} ---")
    rides = []
    try:
        doc = load(filepath)
        for sheet in doc.getElementsByType(Table):
            print(f"Scanning sheet: {sheet.getAttribute('name')}")
            rows = sheet.getElementsByType(TableRow)
            for i, row in enumerate(rows):
                cells = row.getElementsByType(TableCell)
                row_data = []
                for cell in cells:
                    try:
                        row_data.append(get_cell_text(cell))
                    except:
                        row_data.append("")
                
                full_row_str = " ".join(row_data)
                
                # Loose matching for 2025 dates
                if "2025" in full_row_str:
                    date_val = None
                    dist_val = 0.0
                    
                    for col in row_data:
                        # Find date
                        if not date_val and ("2025-" in col or "25-" in col or "2025" in col and len(col) < 12):
                             date_val = col.strip()
                        
                        # Find distance: handle "16.9 km"
                        clean_col = col.lower().replace('km', '').replace(',', '.').strip()
                        if clean_col and clean_col.replace('.', '', 1).isdigit():
                             try:
                                 val = float(clean_col)
                                 # reasonable bike ride > 2km and < 300km
                                 if 2.0 <= val <= 300.0:
                                     dist_val = val
                             except: pass
                    
                    # Extract Speed and Duration (Indices 2 and 4 based on inspection)
                    duration_str = ""
                    speed_val = 0.0
                    if len(row_data) > 4:
                        # Duration at index 2
                        if row_data[2] and len(row_data[2].split('.')) == 3:
                             duration_str = row_data[2].replace('.', ':') # 0.39.52 -> 0:39:52
                        # Speed at index 4
                        try:
                            speed_val = float(row_data[4].replace(',', '.'))
                        except: pass

                    if date_val and dist_val > 0:
                        rides.append({
                            'date': date_val,
                            'distance_km': dist_val,
                            'duration_str': duration_str,
                            'speed_kmh': speed_val,
                            'type': 'Cycling'
                        })
    except Exception as e:
        print(f"Error parsing ODS: {e}")
    
    print(f"Found {len(rides)} bike rides.")
    return rides

def parse_gym_2025(filepath):
    print(f"--- Parsing Gym Data ---")
    workouts = []
    date_pattern = re.compile(r'^25(\d{2})(\d{2})') # YYMMDD where YY=25
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    current_workout = None
    for line in lines:
        line = line.strip()
        if not line: continue
        match = date_pattern.match(line)
        if match:
            if current_workout: workouts.append(current_workout)
            current_workout = {'date': f"2025-{match.group(1)}-{match.group(2)}", 'exercises': []}
        elif current_workout:
            current_workout['exercises'].append(line)
    if current_workout: workouts.append(current_workout)
    return workouts

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def parse_gps_2025(directory):
    print(f"--- Parsing GPS files for 2025 ---")
    stats = []
    files = glob.glob(os.path.join(directory, '*2025*.gpx'))
    
    for fpath in files:
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
            ns = {
                'gpx': 'http://www.topografix.com/GPX/1/1',
                'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
            }
            
            trackpoints = root.findall('.//gpx:trkpt', ns)
            if not trackpoints: continue
            
            total_dist = 0.0
            start_time = None
            end_time = None
            last_valid_point = None
            
            for trkpt in trackpoints:
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
                time_node = trkpt.find('gpx:time', ns)
                
                # Check accuracy
                accuracy = 0.0
                extensions = trkpt.find('gpx:extensions', ns)
                if extensions is not None:
                    tpe = extensions.find('gpxtpx:TrackPointExtension', ns)
                    if tpe is not None:
                        acc_node = tpe.find('gpxtpx:accuracy', ns)
                        if acc_node is not None:
                            try: accuracy = float(acc_node.text)
                            except: pass
                
                if accuracy > 25.0: continue # Skip inaccurate points
                
                t = None
                if time_node is not None:
                    t = datetime.fromisoformat(time_node.text.replace('Z', '+00:00'))
                    if start_time is None: start_time = t
                    end_time = t
                
                if last_valid_point:
                    prev_lat = last_valid_point['lat']
                    prev_lon = last_valid_point['lon']
                    dist = haversine(prev_lat, prev_lon, lat, lon)
                    # Filter supersonic jumps (e.g. > 50km/h = 13.8 m/s)
                    if t and last_valid_point['time']:
                        time_diff = (t - last_valid_point['time']).total_seconds()
                        if time_diff > 0:
                            speed_mps = (dist * 1000) / time_diff
                            if speed_mps < 15.0: # Reasonable limit
                                total_dist += dist
                                last_valid_point = {'lat': lat, 'lon': lon, 'time': t}
                        else:
                             # Duplicate timestamp or zero diff, just update pos if reasonable? 
                             # Safest to ignore distance if time didn't move.
                             last_valid_point = {'lat': lat, 'lon': lon, 'time': t}
                    else:
                        total_dist += dist
                        last_valid_point = {'lat': lat, 'lon': lon, 'time': t}
                else:
                    last_valid_point = {'lat': lat, 'lon': lon, 'time': t}
            
            duration = (end_time - start_time).total_seconds() if start_time and end_time else 0
            
            fname = os.path.basename(fpath)
            parts = fname.split('_')
            # Format: RunnerUp_YYYY-MM-DD-HH-MM-SS_Type.gpx
            raw_type = parts[-1].split('.')[0] if len(parts) >= 3 else "Running"
            
            if "Cycling" in raw_type or "Biking" in raw_type:
                activity_type = "Cycling"
            elif "Walking" in raw_type:
                activity_type = "Walking"
            else:
                activity_type = "Running"
            
            stats.append({
                'date': str(start_time)[:10] if start_time else parts[1][:10],
                'type': activity_type,
                'distance_km': total_dist,
                'duration_sec': duration
            })
        except Exception as e:
            continue
            
    print(f"Found {len(stats)} GPS activities.")
    return stats

def get_more_stats(activities, gym_workouts):
    from collections import defaultdict
    
    # 1. Monthly Breakdown (Stacked)
    # Structure: {1: {'run': 0, 'cycle': 0, 'gym': 0}, ...}
    monthly_counts = defaultdict(lambda: {'run': 0, 'cycle': 0, 'gym': 0, 'walk': 0})
    
    for a in activities:
        if '-' in a['date']:
            try:
                m = int(a['date'].split('-')[1])
                atype = a.get('type', 'Other').lower()
                if 'run' in atype: cat = 'run'
                elif 'cycl' in atype or 'bike' in atype: cat = 'cycle'
                elif 'walk' in atype: cat = 'walk'
                else: cat = 'run' # default fallback
                monthly_counts[m][cat] += 1
            except: pass
            
    for g in gym_workouts:
        if '-' in g['date']:
            try:
                m = int(g['date'].split('-')[1])
                monthly_counts[m]['gym'] += 1
            except: pass

    monthly_data = []
    for m in range(1, 13):
        d = monthly_counts[m]
        monthly_data.append({
            "month": m,
            "run": d['run'],
            "cycle": d['cycle'],
            "gym": d['gym'],
            "walk": d['walk'],
            "total": d['run'] + d['cycle'] + d['gym'] + d['walk']
        })
    
    # 2. Day of Week
    days = []
    all_dates = [a['date'] for a in activities] + [g['date'] for g in gym_workouts]
    for d_str in all_dates:
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            days.append(dt.weekday())
        except: pass
            
    day_counts = defaultdict(int)
    for d in days: day_counts[d] += 1
    
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_data = [{"day": day_names[i], "count": day_counts[i]} for i in range(7)]
    
    # 3. Streaks
    unique_dates = sorted(list(set(all_dates)))
    current_streak = 0
    max_streak = 0
    last_date = None
    
    for d_str in unique_dates:
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d")
            if last_date:
                delta = (d - last_date).days
                if delta == 1:
                    current_streak += 1
                elif delta > 1:
                    max_streak = max(max_streak, current_streak)
                    current_streak = 1
            else:
                current_streak = 1
            last_date = d
        except: pass
    max_streak = max(max_streak, current_streak)

    # 4. Weekly Bests
    # {week_num: {'run_dist': 0, 'cycle_dist': 0}}
    weekly_stats = defaultdict(lambda: {'run_dist': 0.0, 'cycle_dist': 0.0, 'gym_count': 0})
    
    for a in activities:
        try:
            dt = datetime.strptime(a['date'], "%Y-%m-%d")
            week = dt.isocalendar()[1]
            dist = a.get('distance_km', 0)
            atype = a.get('type', '').lower()
            
            if 'run' in atype: weekly_stats[week]['run_dist'] += dist
            elif 'cycl' in atype: weekly_stats[week]['cycle_dist'] += dist
        except: pass

    for g in gym_workouts:
        try:
            dt = datetime.strptime(g['date'], "%Y-%m-%d")
            week = dt.isocalendar()[1]
            weekly_stats[week]['gym_count'] += 1
        except: pass

    best_run_week = max(weekly_stats.items(), key=lambda x: x[1]['run_dist'], default=(0, {'run_dist': 0}))
    best_cycle_week = max(weekly_stats.items(), key=lambda x: x[1]['cycle_dist'], default=(0, {'cycle_dist': 0}))
    
    # Best Gym Month
    best_gym_month_idx = max(range(1, 13), key=lambda m: monthly_counts[m]['gym'], default=1)

    return {
        "monthly": monthly_data,
        "day_of_week": dow_data,
        "longest_streak": max_streak,
        "best_run_week": {"week": best_run_week[0], "distance": best_run_week[1]['run_dist']},
        "best_cycle_week": {"week": best_cycle_week[0], "distance": best_cycle_week[1]['cycle_dist']},
        "best_gym_month": {"month": best_gym_month_idx, "count": monthly_counts[best_gym_month_idx]['gym']}
    }


def generate_wrapped_json():
    cycling_ods = parse_ods_cycling("Cykel 2019 - 2025.ods")
    gym = parse_gym_2025("gym")
    gps_activities = parse_gps_2025("RunnerUp")
    
    # Separate GPS activities
    gps_running = [a for a in gps_activities if a['type'] == 'Running']
    gps_cycling = [a for a in gps_activities if a['type'] == 'Cycling']
    gps_walking = [a for a in gps_activities if a['type'] == 'Walking']
    
    # Deduplicate Cycling: Merge ODS data into GPS data if available
    gps_cycling_dates = set(a['date'] for a in gps_cycling)
    ods_lookup = {c['date']: c for c in cycling_ods}
    
    merged_cycling = []
    # Process GPS rides (inject ODS speed if match found)
    for r in gps_cycling:
        if r['date'] in ods_lookup:
            ods_ride = ods_lookup[r['date']]
            if ods_ride.get('speed_kmh', 0) > 0:
                r['speed_kmh'] = ods_ride['speed_kmh']
        merged_cycling.append(r)
    
    # Add ODS-only rides
    for c in cycling_ods:
        if c['date'] not in gps_cycling_dates:
            merged_cycling.append(c)
            
    all_cycling = merged_cycling
    all_activities = gps_running + all_cycling + gps_walking
    
    extra_stats = get_more_stats(all_activities, gym)
    
    total_km_run = sum(a['distance_km'] for a in gps_running)
    total_km_cycle = sum(a['distance_km'] for a in all_cycling)
    
    # Calculate top 5 runs by distance and speed
    running_with_speed = []
    for r in gps_running:
        if r.get('duration_sec', 0) > 0 and r.get('distance_km', 0) > 0.5: # filter out very short/invalid runs
            duration_sec = r['duration_sec']
            dist_km = r['distance_km']
            
            speed_kmh = (dist_km / duration_sec) * 3600
            
            # Calculate Pace (min/km)
            sec_per_km = duration_sec / dist_km
            mins = int(sec_per_km // 60)
            secs = int(sec_per_km % 60)
            pace_str = f"{mins}:{secs:02d}"
            
            running_with_speed.append({**r, 'speed_kmh': speed_kmh, 'pace': pace_str})
    
    top_5_longest_runs = sorted(gps_running, key=lambda x: x['distance_km'], reverse=True)[:5]
    top_5_fastest_runs = sorted(running_with_speed, key=lambda x: x['speed_kmh'], reverse=True)[:5]

    # Calculate top 5 rides by distance and speed
    cycling_with_speed = []
    for r in all_cycling:
        speed = 0.0
        # Check if speed is already present (from ODS or injected)
        if r.get('speed_kmh', 0) > 0:
            speed = r['speed_kmh']
        # Else calculate from duration (GPS)
        elif r.get('duration_sec', 0) > 0 and r.get('distance_km', 0) > 0.5:
             speed = (r['distance_km'] / r['duration_sec']) * 3600
        
        if speed > 0:
             cycling_with_speed.append({**r, 'speed_kmh': speed})
    
    top_5_longest_rides = sorted(all_cycling, key=lambda x: x['distance_km'], reverse=True)[:5]
    top_5_fastest_rides = sorted(cycling_with_speed, key=lambda x: x['speed_kmh'], reverse=True)[:5]

    wrapped_data = {
        "year": 2025,
        "summary": {
            "total_sessions": len(all_activities) + len(gym),
            "total_km": total_km_run + total_km_cycle,
            "total_km_run": total_km_run,
            "total_km_cycle": total_km_cycle,
            "total_gym": len(gym),
            "total_cardio": len(all_activities),
            "total_hours": sum([a.get('duration_sec', 0) for a in all_activities]) / 3600 # Approx from all GPS + ODS (ODS has no duration, treated as 0 here?)
        },
        "highlights": {
            "longest_run": max([a['distance_km'] for a in gps_running], default=0),
            "longest_ride": max([a['distance_km'] for a in all_cycling], default=0),
            "top_exercises": ["Benböj", "Hantelpress", "Chins"],
            "longest_streak": extra_stats['longest_streak'],
            "best_run_week": extra_stats['best_run_week'],
            "best_cycle_week": extra_stats['best_cycle_week'],
            "best_gym_month": extra_stats['best_gym_month'],
            "top_5_longest_runs": top_5_longest_runs,
            "top_5_fastest_runs": top_5_fastest_runs,
            "top_5_longest_rides": top_5_longest_rides,
            "top_5_fastest_rides": top_5_fastest_rides
        },
        "charts": {
            "monthly": extra_stats['monthly'],
            "day_of_week": extra_stats['day_of_week']
        },
        "gym_log": gym,
        "cardio_log": all_activities
    }
    
    with open('wrapped_data.json', 'w') as f:
        json.dump(wrapped_data, f, indent=2)
    print("Generated wrapped_data.json")
if __name__ == "__main__":
    generate_wrapped_json()
