#!/usr/bin/env python3
"""Route analysis script"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
import app.routers.agent as agent
import app.routers.agent_runs as agent_runs

print("=== AGENT ROUTER ===")
print(f"Router prefix: {agent.router.prefix}")
print("\nRoutes:")
for route in agent.router.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path} - {getattr(route, 'methods', {'UNKNOWN'})}")

print("\n=== AGENT_RUNS ROUTER ===")
print(f"Router prefix: {agent_runs.router.prefix}")
print("\nRoutes:")
for route in agent_runs.router.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path} - {getattr(route, 'methods', {'UNKNOWN'})}")

print("\n=== COMBINED ANALYSIS ===")
app = FastAPI()
app.include_router(agent.router, prefix='/api/v1')
app.include_router(agent_runs.router, prefix='/api/v1')

# Get all routes from the app
all_routes = []
for route in app.routes:
    if hasattr(route, 'path') and 'api/v1' in str(route.path):
        all_routes.append(route)

print(f"Total app routes with /api/v1 prefix: {len(all_routes)}")

# Check for specific expected routes
expected_routes = [
    ('/api/v1/agent/chat', {'POST'}),
    ('/api/v1/agent/execute', {'POST'}),
    ('/api/v1/agent/runs/tools', {'GET'}),
    ('/api/v1/agent/runs/{run_id}', {'GET'}),
    ('/api/v1/agent/runs/run', {'POST'}),
    ('/api/v1/agent/runs/run/{run_id}', {'GET', 'POST', 'DELETE'}),
]

print("\n=== EXPECTED VS ACTUAL ANALYSIS ===")
for expected_path, expected_methods in expected_routes:
    found = False
    for route in all_routes:
        if hasattr(route, 'path') and expected_path.replace('{run_id}', '[0-9a-f]+').replace('{approval_id}', '[0-9a-f]+') in route.path:
            methods = getattr(route, 'methods', set())
            print(f"✓ FOUND: {route.path} - Methods: {methods}")
            found = True
            break
    
    if not found:
        print(f"✗ MISSING: Expected {expected_path} with methods {expected_methods}")