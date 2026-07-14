import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_system_metrics(
    projects: list, deployments: list, incidents: list, adrs: list,
    seed_date=datetime(2021, 1, 1), end_date=datetime(2025, 12, 31)
):
    """
    Generates a continuous time-series history of system metrics for each project,
    correlating with ADR deployments and incidents.
    """
    all_metrics = []
    
    # Range of dates
    num_days = (end_date - seed_date).days + 1
    dates = [seed_date + timedelta(days=d) for d in range(num_days)]
    
    # Organize deployments and incidents by project
    deps_by_proj = {p["project_id"]: [] for p in projects}
    for d in deployments:
        # We need to trace deployment back to project via PR
        if d["linked_pr"]:
            # Check projects in deployments (will map by project name / repository)
            proj_obj = next((p for p in projects if p["repository"] == d["pipeline_run"].split("/")[-3]), None)
            if proj_obj:
                deps_by_proj[proj_obj["project_id"]].append(d)
                
    incs_by_proj = {p["project_id"]: [] for p in projects}
    for inc in incidents:
        proj_obj = next((p for p in projects if p["name"] == inc["_project_name"]), None)
        if proj_obj:
            incs_by_proj[proj_obj["project_id"]].append(inc)
            
    # Track ADR impacts on baseline metrics per project
    # adr_impacts[project_id] = { 'latency': multiplier, 'availability': delta, 'cost': multiplier }
    adr_impacts = {p["project_id"]: {"latency": 1.0, "availability": 0.0, "cost": 1.0, "error_rate": 1.0} for p in projects}
    
    # Map deployments of ADRs to their dates
    adr_deployments = []
    for d in deployments:
        if d["linked_adr"] and d["status"] == "Success" and d["environment"] == "production":
            dep_dt = datetime.strptime(d["timestamp"], "%Y-%m-%d %H:%M:%S")
            adr_deployments.append({
                "project_id": d["pipeline_run"].split("/")[-3], # repo mapping helper
                "adr_id": d["linked_adr"],
                "date": dep_dt,
                "deployment_id": d["deployment_id"]
            })
            
    # Generate day-by-day metrics
    for dt in dates:
        dt_str = dt.strftime("%Y-%m-%d")
        is_weekend = dt.weekday() >= 5
        
        # Apply any ADR improvements that were deployed before this date
        for adr_dep in adr_deployments:
            if dt >= adr_dep["date"]:
                # Find the ADR details
                adr_obj = next((a for a in adrs if a["adr_id"] == adr_dep["adr_id"]), None)
                if adr_obj and "_impact_applied" not in adr_obj:
                    # Apply impact factor
                    p_id = adr_obj["related_project"]
                    metric = adr_obj["_impact_metric"]
                    direction = adr_obj["_impact_direction"]
                    val = adr_obj["_impact_val"]
                    
                    if metric == "latency":
                        if direction == "decrease":
                            adr_impacts[p_id]["latency"] *= (1.0 - val / 100.0)
                    elif metric == "availability":
                        if direction == "increase":
                            adr_impacts[p_id]["availability"] = min(0.009, adr_impacts[p_id]["availability"] + val)
                    elif metric == "cost":
                        if direction == "increase":
                            adr_impacts[p_id]["cost"] *= (1.0 + val / 100.0)
                        elif direction == "decrease":
                            adr_impacts[p_id]["cost"] *= (1.0 - val / 100.0)
                            
                    # Mark as applied so we don't multiply multiple times (this is global but tracked per adr)
                    adr_obj["_impact_applied"] = True
                    
        # Process each project
        for proj in projects:
            p_id = proj["project_id"]
            p_name = proj["name"]
            
            # Baseline parameters
            traffic_baseline = 1000.0  # RPM
            # Business growth factor: traffic increases slowly over 5 years
            years_elapsed = (dt - seed_date).days / 365.25
            growth_factor = 1.0 + (years_elapsed * 0.4) # 40% growth per year
            
            # Traffic seasonality
            traffic = traffic_baseline * growth_factor
            if is_weekend:
                traffic *= random.uniform(0.4, 0.6) # Lower weekend traffic
            else:
                traffic *= random.uniform(0.8, 1.2)
                
            # Metric baselines
            cpu_base = 35.0 + (traffic / 500.0) # CPU grows with traffic
            cpu = np.clip(cpu_base + random.uniform(-5.0, 5.0), 5.0, 95.0)
            
            mem_base = 50.0 + (traffic / 800.0)
            mem = np.clip(mem_base + random.uniform(-3.0, 3.0), 10.0, 90.0)
            
            # Latency baseline, adjusted by ADR impacts
            latency_base = 150.0 * adr_impacts[p_id]["latency"]
            latency = latency_base + random.uniform(-15.0, 15.0)
            
            # Availability baseline, adjusted by ADR
            avail_base = 99.9 + adr_impacts[p_id]["availability"]
            availability = min(100.0, avail_base - max(0.0, random.uniform(0.0, 0.05)))
            
            # Error Rate baseline
            error_rate = max(0.0, 0.05 + random.uniform(-0.02, 0.03))
            
            # Daily Cost
            cost_base = 50.0 * adr_impacts[p_id]["cost"] * growth_factor
            cost = cost_base + random.uniform(-2.0, 2.0)
            
            # Overlay incident anomalies if an incident occurred on this day
            project_incidents = incs_by_proj[p_id]
            day_has_incident = False
            inc_obj_active = None
            
            for inc in project_incidents:
                if inc["_detect_time"].strftime("%Y-%m-%d") == dt_str:
                    day_has_incident = True
                    inc_obj_active = inc
                    break
                    
            if day_has_incident and inc_obj_active:
                # Spike metrics!
                severity = inc_obj_active["severity"]
                if severity == "P0":
                    latency = random.uniform(3000.0, 8000.0)
                    availability = random.uniform(85.0, 94.0)
                    error_rate = random.uniform(8.0, 20.0)
                    cpu = random.uniform(90.0, 99.0)
                elif severity == "P1":
                    latency = random.uniform(800.0, 2500.0)
                    availability = random.uniform(95.0, 98.5)
                    error_rate = random.uniform(3.0, 8.0)
                    cpu = random.uniform(80.0, 95.0)
                else: # P2/P3
                    latency = random.uniform(400.0, 1200.0)
                    availability = random.uniform(98.5, 99.5)
                    error_rate = random.uniform(1.0, 3.0)
                    cpu = random.uniform(70.0, 85.0)
                    
            all_metrics.append({
                "date": dt_str,
                "project_id": p_id,
                "project_name": p_name,
                "cpu_usage_pct": round(float(cpu), 2),
                "memory_usage_pct": round(float(mem), 2),
                "latency_ms": round(float(latency), 1),
                "availability_pct": round(float(availability), 3),
                "error_rate_pct": round(float(error_rate), 3),
                "traffic_rpm": round(float(traffic), 0),
                "daily_cost_usd": round(float(cost), 2)
            })
            
    return all_metrics

def write_incident_high_res_metrics(incidents: list, output_dir_path):
    """
    Creates individual hourly metrics logs for incident days in monitoring/incidents/
    to show high-resolution logs.
    """
    inc_metrics_dir = output_dir_path / "monitoring"
    inc_metrics_dir.mkdir(parents=True, exist_ok=True)
    
    for inc in incidents:
        inc_id = inc["incident_id"]
        detect_time = inc["_detect_time"]
        proj_name = inc["_project_name"]
        
        # Hours of the day
        rows = []
        for hour in range(24):
            dt_hour = datetime(detect_time.year, detect_time.month, detect_time.day, hour, 0, 0)
            dt_hour_str = dt_hour.strftime("%Y-%m-%d %H:%M:%S")
            
            # Baseline metrics
            cpu = random.uniform(30, 45)
            mem = random.uniform(50, 60)
            latency = random.uniform(80, 150)
            availability = random.uniform(99.9, 100.0)
            error_rate = random.uniform(0.01, 0.05)
            traffic = random.uniform(800, 1200)
            
            # Check if this hour overlaps with the incident duration (detect to resolve)
            is_anomaly = False
            if detect_time.hour <= hour <= inc["_resolve_time"].hour:
                is_anomaly = True
                
            if is_anomaly:
                severity = inc["severity"]
                if severity == "P0":
                    cpu = random.uniform(92, 99)
                    latency = random.uniform(4000, 9000)
                    availability = random.uniform(80, 92)
                    error_rate = random.uniform(10, 25)
                elif severity == "P1":
                    cpu = random.uniform(85, 96)
                    latency = random.uniform(1500, 3000)
                    availability = random.uniform(94, 98)
                    error_rate = random.uniform(4, 10)
                else:
                    cpu = random.uniform(75, 88)
                    latency = random.uniform(500, 1200)
                    availability = random.uniform(98, 99.5)
                    error_rate = random.uniform(1, 4)
                    
            rows.append({
                "timestamp": dt_hour_str,
                "cpu_usage_pct": round(cpu, 2),
                "memory_usage_pct": round(mem, 2),
                "latency_ms": round(latency, 1),
                "availability_pct": round(availability, 3),
                "error_rate_pct": round(error_rate, 3),
                "traffic_rpm": round(traffic, 0)
            })
            
        # Write to csv
        df = pd.DataFrame(rows)
        csv_file = inc_metrics_dir / f"metrics_{inc_id}.csv"
        df.to_csv(csv_file, index=False)
