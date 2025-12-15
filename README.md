# NTUT_EmbeddingSystemFinal

This project is a smart AIoT traffic monitoring system that combines Edge Computing and cloud microservices.

It utilizes a Raspberry Pi Pico 2 W as the edge capture device to monitor traffic in real-time. The captured images are uploaded to a backend server where computer vision technology automatically detects vehicles illegally parked in red zones.

## Quick Start

This project is fully containerized. Please ensure **Docker** and **Docker Compose** are installed in your environment.

### IoT Device Simulation

Since the **Raspberry Pi Pico 2 W** acts as the data source, we provide a simulation script for development without the physical hardware:

**mock_pico.py**: Simulates the Pico's behavior by periodically sending test images to the backend API, allowing full system testing (Frontend -> Backend -> AI) without the actual embedded device.

### Start Services

Run the following command in the project root directory:

```bash
docker-compose up -d
````

The system will automatically build and start the following services:

  * **Frontend (User Interface)**: http://localhost:5173
  * **Backend (API Docs)**: http://localhost:8000/docs
  * **AI Service (Mock Service)**: http://localhost:5000/docs

### Stop Services

```bash
docker-compose down
```

## System Features

1.  **Real-time Dashboard**

      * Provides live image streaming.
      * Displays real-time system status (Safe / Detecting Violation) and visualized AI inference results.

2.  **Manual Test**

      * Provides an image upload interface to simulate the AI analysis process.
      * Returns detailed detection data.

3.  **Violation History**

      * Automatically saves evidence images when a violation occurs.
      * Records the violation timestamp, reason, and detailed status.
      * Provides a grid-view interface for browsing history.

## System Architecture

The system adopts a **Cloud-Edge Collaboration** design:

* **Edge Device (Pi Pico 2 W)**: Captures real-time traffic images via a camera module and uploads them via Wi-Fi.
* **AI Service**: Uses YOLO object detection and semantic segmentation.
* **Backend**: Handles business logic, IoU calculation, database access, and image processing.
* **Frontend**: Handles data visualization and user interaction.

## Tech Stack

* **Hardware / Edge**: Raspberry Pi Pico 2 W, Camera Module (OV7670)
* **Firmware**: CircuitPython
* **Frontend**: Vue 3, Vite, Tailwind CSS
* **Backend**: FastAPI
* **Database**: PostgreSQL
* **Infrastructure**: Docker, Docker Compose

## Project Structure

```text
NTUT_EmbeddingSystemFinal/
│
├── mock_pico.py             # IoT Edge Device Simulation (Simulates Pi Pico2 W behavior)
├── docker-compose.yml       # Container orchestration config
├── .gitignore               # Git ignore settings
│
├── ai_service/              # AI Service (YOLO)
│   ├── Dockerfile           # Docker image config for AI service
│   ├── environment.yaml     # Python dependency list
│   └── mock_yolo.py         # Core logic: Simulates vehicle detection & red line segmentation
│
├── backend/                 # Backend API Service (FastAPI)
│   ├── Dockerfile           # Docker image config for Backend
│   ├── main.py              # API Entry: Handles image uploads & violation logic
│   ├── models.py            # Database models definition (SQLAlchemy)
│   ├── database.py          # Database connection settings
│   └── static/              # Static file storage
│       └── uploads/         # Storage for violation evidence images
│
└── frontend/                # Frontend Interface (Vue 3 + Vite)
    ├── Dockerfile           # Docker image config for Frontend
    ├── package.json         # NPM dependency list
    ├── vite.config.js       # Vite build configuration
    ├── index.html           # HTML entry point
    └── src/
        ├── main.js          # Vue application entry
        ├── App.vue          # Root component
        ├── router.js        # Vue Router configuration
        ├── components/      # Shared components
        │   └── navbar.vue   # Navigation bar
        └── views/           # Page components
            ├── index.vue    # Dashboard (Live monitoring)
            ├── upload.vue   # UploadTest (Manual testing page)
            └── history.vue  # History (Violation records page)
```
