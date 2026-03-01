import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from datetime import datetime

# Load env vars from apps/web/.env.local (or apps/server/.env if preferred)
load_dotenv("../web/.env.local")

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials in .env.local")
    exit(1)

supabase: Client = create_client(url, key)

CASE_ID = "TN-2026-00417"

def seed_data():
    print(f"--- Seeding test data for Case {CASE_ID} ---")
    
    # 1. Clear old data for a clean slate
    print("Clearing old data...")
    supabase.table("incident_state").delete().eq("case_id", CASE_ID).execute()
    supabase.table("agent_logs").delete().eq("case_id", CASE_ID).execute()
    supabase.table("transcripts").delete().eq("case_id", CASE_ID).execute()
    supabase.table("dispatches").delete().eq("case_id", CASE_ID).execute()
    
    # 2. Insert Initial State (Intake)
    print("Inserting Initial Incident State...")
    supabase.table("incident_state").insert({
        "case_id": CASE_ID,
        "status": "intake",
        "severity": "unknown",
        "caller_count": 0,
        "people_count_estimate": 0,
        "injury_flags": [],
        "hazard_flags": [],
        "vision_detections": [],
        "recommended_units": [],
        "confirmed_units": [],
        "action_plan_version": 0,
        "action_plan": []
    }).execute()
    
    print("Inserted Initial State. Check UI.")
    time.sleep(3)
    
    # 3. Simulate Caller 1 + Triage agent
    print("Simulating Caller 1 (Spanish) + Triage Update...")
    supabase.table("transcripts").insert({
        "case_id": CASE_ID,
        "caller_id": "Caller 1",
        "caller_label": "Caller 1 (ES)",
        "language": "es",
        "original_text": "Market and 5th. Mi esposo está atrapado en el auto.",
        "translated_text": "Market and 5th. My husband is trapped in the car.",
        "entities": ["Market and 5th", "trapped"],
        "segment_index": 0
    }).execute()
    
    supabase.table("agent_logs").insert({
        "case_id": CASE_ID,
        "agent": "TriageAgent",
        "event_type": "facts_extracted",
        "message": "Extracted location (Market & 5th) and trapped occupant flag. Severity HIGH.",
        "display_color": "purple",
        "display_flash": True,
        "data": {}
    }).execute()
    
    supabase.table("incident_state").update({
        "status": "active",
        "incident_type": "vehicle_collision",
        "location_raw": "Market and 5th",
        "location_normalized": "Market St & 5th St",
        "severity": "high",
        "caller_count": 1,
        "people_count_estimate": 2,
        "injury_flags": ["trapped_occupant"],
        "recommended_units": ["EMS", "Traffic Control"],
        "action_plan_version": 1
    }).eq("case_id", CASE_ID).execute()
    
    supabase.table("dispatches").insert([
        {
            "case_id": CASE_ID,
            "unit_type": "EMS",
            "status": "recommended",
            "language": "en"
        },
        {
            "case_id": CASE_ID,
            "unit_type": "Traffic Control",
            "status": "recommended",
            "language": "en"
        }
    ]).execute()
    
    print("Inserted Phase 1 Update. Check UI for Transcript, Case File, and Response Lanes.")
    time.sleep(4)
    
    # 4. Simulate Action Approval
    print("Simulating Human Approval...")
    supabase.table("agent_logs").insert({
        "case_id": CASE_ID,
        "agent": "Orchestrator",
        "event_type": "operator_approval",
        "message": "Operator approved initial response plan.",
        "display_color": "green",
        "display_flash": False,
        "data": {}
    }).execute()

    # Update dispatches to confirmed
    supabase.table("dispatches").update({"status": "confirmed"}).eq("case_id", CASE_ID).in_("unit_type", ["EMS", "Traffic Control"]).execute()
    
    supabase.table("incident_state").update({
        "confirmed_units": ["EMS", "Traffic Control"]
    }).eq("case_id", CASE_ID).execute()

    print("Updated Phase 2 Approval. Check UI for Response Lanes turning bright/Confirmed.")
    time.sleep(3)

    # 5. Simulate Caller 2 (Escalation)
    print("Simulating Caller 2 (Mandarin) + Intelligence Fusion...")
    supabase.table("transcripts").insert({
        "case_id": CASE_ID,
        "caller_id": "Caller 2",
        "caller_label": "Caller 2 (ZH)",
        "language": "zh",
        "original_text": "后座有个孩子！",
        "translated_text": "There is a child in the back seat!",
        "entities": ["child"],
        "segment_index": 0
    }).execute()

    supabase.table("agent_logs").insert({
        "case_id": CASE_ID,
        "agent": "EvidenceFusion",
        "event_type": "severity_delta",
        "message": "Correlated new caller to case (0.94). Child detected. Escalating severity to CRITICAL.",
        "display_color": "red",
        "display_flash": True,
        "data": {}
    }).execute()

    supabase.table("incident_state").update({
        "status": "critical",
        "severity": "critical",
        "caller_count": 2,
        "people_count_estimate": 3,
        "hazard_flags": ["child_present", "trapped_occupant"],
        "recommended_units": ["EMS", "Traffic Control", "Pediatric EMS"],
        "action_plan_version": 2
    }).eq("case_id", CASE_ID).execute()

    supabase.table("dispatches").insert({
        "case_id": CASE_ID,
        "unit_type": "Pediatric EMS",
        "status": "recommended",
        "language": "en"
    }).execute()

    print("Inserted Phase 3 update. UI should show CRITICAL, new transcript, and Pediatric EMS lane.")
    time.sleep(4)

    # 6. Simulate Vision Detections (Fire)
    print("Simulating Pixtral Vision Detections (Engine Fire)...")
    supabase.table("agent_logs").insert({
        "case_id": CASE_ID,
        "agent": "VisionAgent",
        "event_type": "hazard_detected",
        "message": "Visual analysis detected engine fire (0.99). Dispatching Fire Response.",
        "display_color": "amber",
        "display_flash": True,
        "data": {}
    }).execute()

    supabase.table("incident_state").update({
        "vision_detections": [
            {"label": "smoke", "confidence": 0.88, "engine_fire": False},
            {"label": "engine fire", "confidence": 0.99, "engine_fire": True}
        ],
        "hazard_flags": ["child_present", "trapped_occupant", "engine_fire"],
        "recommended_units": ["EMS", "Traffic Control", "Pediatric EMS", "Fire Response"],
        "action_plan_version": 3
    }).eq("case_id", CASE_ID).execute()

    supabase.table("dispatches").insert({
        "case_id": CASE_ID,
        "unit_type": "Fire Response",
        "status": "recommended",
        "language": "en"
    }).execute()

    print("Inserted Phase 4 vision update. CCTV Panel should flash RED with Fire overlay.")
    print("Test complete. Check UI.")

if __name__ == "__main__":
    seed_data()
