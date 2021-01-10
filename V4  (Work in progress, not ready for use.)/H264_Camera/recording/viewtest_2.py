#!/usr/bin/env python3

import asyncio
import websockets
import json
import base64
import numpy as np
from PIL import Image
import io
import cv2


async def hello(uri):
    async with websockets.connect(uri) as websocket:
        while(True):
            msg=await websocket.recv()
            print(msg)
            decoded = base64.deco
            print(decoded)
            exit()
            # json_msg=json.loads(msg)
            # if json_msg['type']=='image':
            #     buffer=json_msg['buffer']
            #     base64_decoded = base64.b64decode(buffer)
            #     image = Image.open(io.BytesIO(base64_decoded))
            #     image = np.array(image)
            #     cv2.imshow('Video stream using Websocket',image)
            #     if cv2.waitKey(1) & 0xFF == ord('q'):
            #         break

        cv2.destroyAllWindows()

asyncio.get_event_loop().run_until_complete(
    hello('ws://192.168.178.207:8000/ws/'))