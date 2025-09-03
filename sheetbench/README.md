# sheetbench


## Quick Start


```bash

$ buckeye init sheetbench

$ buckeye dev --build --inspector

or,  build the image and hot reload
$ buckeye dev . --build

Debug it with the CLI to see if it launches: (4/5 phases passed, MCP issues, debug.txt has the report)
$ buckeye debug sheetbench:dev


Analyze it to see if all tools appear: (need to pull it first, but live analysis works)
$ buckeye analyze sheetbench:dev




buckeye-python/sheetbench/src/controller$ python hf_eval.py hud-evals/SheetBench-50 --agent claude --full --max-steps 100 --verbose




Test:
$ buckeye dev . --build
and another terminal you can test it, before check the MCP is active in cursor, MOCKUP CURL request
buckeye-python/sheetbench/src/controller$ curl -v -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' http://localhost:8765/mcp
Note: Unnecessary use of -X or --request, POST is already inferred.
* Host localhost:8765 was resolved.
* IPv6: ::1
* IPv4: 127.0.0.1
*   Trying [::1]:8765...
* connect to ::1 port 8765 from ::1 port 40244 failed: Connection refused
*   Trying 127.0.0.1:8765...
* Connected to localhost (127.0.0.1) port 8765
> POST /mcp HTTP/1.1
> Host: localhost:8765
> User-Agent: curl/8.5.0
> Content-Type: application/json
> Accept: application/json, text/event-stream
> Content-Length: 151
> 
< HTTP/1.1 200 OK
< date: Wed, 03 Sep 2025 20:00:16 GMT
< server: uvicorn
< cache-control: no-cache, no-transform
< connection: keep-alive
< content-type: text/event-stream
< mcp-session-id: f8cd079e40ef48db9ee9f18528e22a67
< x-accel-buffering: no
< Transfer-Encoding: chunked
< 
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"prompts":{"listChanged":true},"resources":{"subscribe":false,"listChanged":true},"tools":{"listChanged":true}},"serverInfo":{"name":"buckeye dev Proxy - sheetbench:dev","version":"1.13.1"}}}

* Connection #0 to host localhost left intact


When I try this test code:
$ python -c "from datasets import load_dataset; ds = load_dataset('hud-evals/SheetBench-50', split='train'); print('Task keys:', list(ds[0].keys())); print('MCP config:', ds[0].get('mcp_config', 'No mcp_config'))"
Task keys: ['prompt', 'mcp_config', 'id', 'metadata', 'setup_tool', 'evaluate_tool', 'system_prompt']
MCP config: {"hud": {"url": "https://mcp.hud.so/v3/mcp", "headers": {"Authorization": "Bearer ${HUD_API_KEY}", "Mcp-Image": "hudevals/hud-remote-browser:0.1.0"}}}