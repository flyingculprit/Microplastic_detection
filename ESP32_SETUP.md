# ESP32 CAM Setup & Integration Guide

This document explains how to set up your ESP32 CAM to work with the Microplastic Detection AI and how the integration is implemented.

## 1. ESP32 CAM Firmware Requirements

Your ESP32 CAM must be running a web server that provides a snapshot at the `/capture` endpoint.

### Sample Arduino/ESP32 Code Structure
```cpp
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

WebServer server(80);

void handleCapture() {
  Serial.println("Capture requested...");

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  Serial.printf("Image size: %d bytes\n", fb->len);

  // The WebServer library's send() method handles Content-Length and binary data automatically.
  // Do NOT use client.write() or manual Content-Length headers as they conflict with server.send().
  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.send(200, "image/jpeg", (const char *)fb->buf, fb->len);

  esp_camera_fb_return(fb);
  Serial.println("Image sent successfully");
}

void setup() {
  // ... Camera and WiFi initialization ...
  server.on("/capture", HTTP_GET, handleTakeSnap);
  server.begin();
}

void loop() {
  server.handleClient();
}
```

## 2. Infrastructure Flow

The integration bridges your local ESP32 CAM with the Gemini-powered analysis server:

1.  **Configuration**: The user sets the ESP32 IP address via the `/setup` page. This is saved in `config.json`.
2.  **Trigger**: Clicking **Detect Live** on the home page hits the `/detect-live` route in `genapp.py`.
3.  **Capture**: The Python server sends a GET request to `http://<ESP32_IP>/capture`.
4.  **Processing**:
    - The received JPEG is saved to the `static/` folder.
    - `analyze_and_detect()` sends the image to Gemini.
    - `draw_bounding_boxes()` overlays the detected plastics.
5.  **Display**: The UI refreshes to show the live snapshot alongside the AI analysis report.

## 3. Key Files Added/Modified

| File | Purpose |
| :--- | :--- |
| `config.json` | Stores the ESP32 CAM IP address. |
| `genapp.py` | Added `/setup` and `/detect-live` routes + config handling. |
| `templates/setup.html` | Hidden page to update the IP address. |
| `templates/home.html` | Added side-by-side buttons for Upload and Live Detection. |
| `static/script.js` | Added "Connecting to ESP32 CAM..." loading state. |

## 4. Connection Troubleshooting
- **Network**: Ensure both the ESP32 and the computer running `genapp.py` are on the same WiFi network.
- **Port**: The code assumes the default port 80. If your ESP32 uses a different port, update the URL in `genapp.py`.
- **IP Address**: Use the `/setup` page to update the IP whenever it changes.
