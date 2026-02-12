#!/usr/bin/env python3
"""Test MCP server - handles stderr logging properly"""

import subprocess
import json
import sys
import time

def test_mcp_server():
    """Test the MCP server by sending JSON-RPC requests via stdin"""
    
    print("🚀 Starting MCP server...\n")
    
    # Start the server process
    process = subprocess.Popen(
        ["uv", "run", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give server a moment to start
    time.sleep(0.5)
    
    try:
        # Initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response (skip empty lines)
        response_line = ""
        while not response_line.strip():
            response_line = process.stdout.readline()
            if not response_line:
                print("❌ No response from server")
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"Server stderr:\n{stderr_output}")
                return
        
        try:
            init_response = json.loads(response_line)
            print("✅ Server initialized")
            print(f"   Protocol: {init_response.get('result', {}).get('protocolVersion', 'N/A')}")
            print(f"   Server: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse init response: {e}")
            print(f"   Raw response: {response_line}")
            return
        
        print("\n" + "="*70)
        
        # List tools request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("📤 Requesting tools list...\n")
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = ""
        while not response_line.strip():
            response_line = process.stdout.readline()
            if not response_line:
                print("❌ No response from server")
                return
        
        try:
            tools_response = json.loads(response_line)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse tools response: {e}")
            print(f"   Raw response: {response_line}")
            return
        
        # Display tools
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            print(f"🔧 Found {len(tools)} available tools:\n")
            print("="*70)
            
            for i, tool in enumerate(tools, 1):
                print(f"\n{i}. 📦 {tool['name']}")
                print(f"   {tool.get('description', 'No description')}")
                
                if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                    props = tool['inputSchema']['properties']
                    required = tool['inputSchema'].get('required', [])
                    
                    if props:
                        print(f"   Parameters:")
                        for param_name, param_info in props.items():
                            param_type = param_info.get('type', 'any')
                            is_required = param_name in required
                            req_text = "required" if is_required else "optional"
                            desc = param_info.get('description', '')
                            
                            print(f"     • {param_name} ({param_type}, {req_text})")
                            if desc:
                                print(f"       {desc}")
                else:
                    print(f"   No parameters")
            
            print("\n" + "="*70)
            print(f"✅ Successfully listed {len(tools)} tools!")
            
        elif "error" in tools_response:
            print("❌ Error response:")
            print(json.dumps(tools_response["error"], indent=2))
        else:
            print("❌ Unexpected response format:")
            print(json.dumps(tools_response, indent=2))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        process.terminate()
        process.wait(timeout=2)

if __name__ == "__main__":
    test_mcp_server()