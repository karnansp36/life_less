# test_websocket_simple.py
import asyncio
import websockets
import json

async def test_websocket():
    try:
        async with websockets.connect('ws://localhost:8000/ws/chat/1/test-session-123') as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            message = json.dumps({
                "message": "Hello, can you hear me?",
                "type": "chat"
            })
            await websocket.send(message)
            print(f"📤 Sent: {message}")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"📥 Received: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())