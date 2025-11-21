#!/usr/bin/env python3
"""
AI Endpoints Test Script
Tests all AI-powered endpoints to verify fixes are working
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(name: str, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"  Endpoint: {method} {endpoint}")
    print(f"  URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
        
        http_code = response.status_code
        response_time = response.elapsed.total_seconds()
        
        try:
            body = response.json()
            is_json = True
        except:
            body = response.text
            is_json = False
        
        print(f"  HTTP Code: {http_code}")
        print(f"  Response Time: {response_time:.2f}s")
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "http_code": http_code,
            "response_time": response_time,
            "is_json": is_json,
            "success": False,
            "error": None,
        }
        
        if http_code == 200:
            if is_json:
                # Check for success indicators
                if isinstance(body, dict):
                    has_success = body.get("success") or "success" in str(body).lower()
                    has_error = "error" in str(body).lower() and not has_success
                    has_data = "data" in body or "career_paths" in body or "emerging_skills" in body or "team_summary" in body
                    
                    if has_error:
                        result["success"] = False
                        result["error"] = body.get("error", "Unknown error")
                        print(f"  Status: ❌ FAILED - {result['error']}")
                        print(f"  Response keys: {list(body.keys())[:5]}")
                    elif has_success or has_data:
                        result["success"] = True
                        result["data"] = body
                        print(f"  Status: ✅ PASSED")
                        print(f"  Response keys: {list(body.keys())[:5]}")
                    else:
                        result["success"] = False
                        result["error"] = "No clear success indicator"
                        print(f"  Status: ⚠️  WARNING - No clear success indicator")
                        print(f"  Response: {str(body)[:200]}")
                else:
                    result["success"] = False
                    result["error"] = "Response is not a dict"
                    print(f"  Status: ❌ FAILED - Response is not a dict")
            else:
                result["success"] = False
                result["error"] = "Invalid JSON"
                print(f"  Status: ❌ FAILED - Invalid JSON")
                print(f"  Response: {body[:200]}")
        else:
            result["success"] = False
            result["error"] = f"HTTP {http_code}"
            print(f"  Status: ❌ FAILED - HTTP {http_code}")
            if is_json and isinstance(body, dict):
                print(f"  Error: {body.get('error', body.get('detail', 'Unknown'))}")
            else:
                print(f"  Response: {str(body)[:200]}")
        
        return result
        
    except requests.exceptions.Timeout:
        result = {
            "name": name,
            "endpoint": endpoint,
            "success": False,
            "error": "Timeout (>30s)",
        }
        print(f"  Status: ❌ FAILED - Timeout")
        return result
    except Exception as exc:
        result = {
            "name": name,
            "endpoint": endpoint,
            "success": False,
            "error": str(exc),
        }
        print(f"  Status: ❌ FAILED - {exc}")
        return result

def main():
    """Run all tests."""
    print("="*60)
    print("AI ENDPOINTS TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Skill Analysis (was failing with truncation)
    print("\n1. TESTING SKILL ANALYSIS (Was failing with truncation)")
    results.append(test_endpoint("Skill Analysis - Employee 9186", "GET", "/api/skills/analysis/9186"))
    results.append(test_endpoint("Skill Analysis - Employee 14607", "GET", "/api/skills/analysis/14607"))
    
    # Test 2: Hackathon AI endpoints (have fallback)
    print("\n2. TESTING HACKATHON AI ENDPOINTS (Have fallback)")
    results.append(test_endpoint("Career Path - Employee 9186", "GET", "/api/hackathons/employee/9186/career-path"))
    results.append(test_endpoint("5-Year Forecast", "GET", "/api/hackathons/forecast/skills-5y"))
    
    # Test 3: Other AI endpoints
    print("\n3. TESTING OTHER AI ENDPOINTS")
    results.append(test_endpoint("Team Intel - SE", "GET", "/api/ai/team-intel/SE"))
    results.append(test_endpoint("Employee Intel - 9186", "GET", "/api/ai/employee-intel/9186"))
    results.append(test_endpoint("Succession Intel - SE", "GET", "/api/ai/succession-intel/SE"))
    
    # Test 4: Career Coach Chat
    print("\n4. TESTING CAREER COACH CHAT")
    results.append(test_endpoint("Career Chat", "POST", "/api/ai/career-chat", {"message": "What skills should I develop?"}))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    if failed > 0:
        print("FAILED TESTS:")
        for r in results:
            if not r.get("success"):
                print(f"  - {r['name']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

