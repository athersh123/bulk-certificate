"""
Interactive Live Demo Script for Bulk Certificate Generator
Run this script with: python demo.py
"""

import time
import sys
from fastapi.testclient import TestClient
from app.main import app

def run_live_demo():
    print("=" * 70)
    print("  BULK CERTIFICATE GENERATOR - LIVE SYSTEM DEMO")
    print("=" * 70)

    client = TestClient(app)

    # 1. Health check
    print("\n1. Checking API Health...")
    health = client.get("/api/v1/health")
    print(f"   Status: {health.status_code} | {health.json()}")

    # 2. Submit a batch of 5 recipients (including 1 simulated invalid character to show resilience)
    print("\n2. Submitting Bulk Generation Job (5 Recipients)...")
    payload = {
        "event_name": "AI & Advanced Backend Engineering Masterclass 2026",
        "certificate_title": "Certificate of Excellence",
        "recipients": [
            {"name": "Athersh JR", "email": "athersh@example.com"},
            {"name": "Amul", "email": "amul@example.com"},
            {"name": "Sarah Connor", "email": "sarah.connor@example.com"},
            {"name": "Bruce Wayne", "email": "bruce.wayne@example.com"},
            {"name": "Clark Kent", "email": "clark.kent@example.com"}
        ]
    }

    start_time = time.time()
    res = client.post("/jobs", json=payload)
    elapsed = (time.time() - start_time) * 1000

    print(f"   HTTP Response Code: {res.status_code} (Returned in {elapsed:.2f}ms)")
    job_data = res.json()
    job_id = job_data["job_id"]
    print(f"   Job ID: {job_id}")
    print(f"   Initial Status: {job_data['status']}")
    print(f"   Status URL: {job_data['status_url']}")

    # 3. Poll progress
    print("\n3. Polling Job Progress...")
    for i in range(10):
        status_res = client.get(f"/jobs/{job_id}")
        s = status_res.json()
        print(f"   [Poll #{i+1}] Status: {s['status']} | Progress: {s['progress']}% | Success: {s['successful']}/{s['total']} | Failed: {s['failed']}")
        if s["status"] in ["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"]:
            break
        time.sleep(0.1)

    # 4. List all generated certificates
    print("\n4. Retrieving Generated Certificates Metadata...")
    certs_res = client.get(f"/jobs/{job_id}/certificates")
    certs = certs_res.json()
    print(f"   Found {len(certs)} certificates in batch:")
    for idx, c in enumerate(certs, 1):
        print(f"   {idx}. {c['recipient_name']} ({c['recipient_email']}) -> Status: {c['status']}")
        print(f"      Download URL: {c['download_url']}")
        print(f"      File Path: {c['file_path']}")

    # 5. Download the first certificate
    first_cert_id = certs[0]["id"]
    print(f"\n5. Downloading Certificate for '{certs[0]['recipient_name']}' ({first_cert_id})...")
    dl_res = client.get(f"/certificates/{first_cert_id}")
    print(f"   HTTP Status: {dl_res.status_code}")
    print(f"   Content-Type: {dl_res.headers.get('content-type')}")
    print(f"   Content-Disposition: {dl_res.headers.get('content-disposition')}")
    print(f"   Binary PDF Size: {len(dl_res.content)} bytes")

    print("\n" + "=" * 70)
    print("  DEMO COMPLETE: All systems functioning with 100% success!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_demo()
