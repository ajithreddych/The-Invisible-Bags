# Rice Mill AI – System Design Document

## 1. High-Level Architecture

The system follows a three-tier architecture with an AI processing pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                        │
│  HTML + CSS + JavaScript (Vanilla)                          │
│  - Bill Registration Form                                    │
│  - AI Verification Interface                                 │
│  - Verified Bills View                                       │
│  - Fraud Alerts View                                         │
│  - All Records View                                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│                       BACKEND LAYER                          │
│  Python Flask Application                                    │
│  - API Routes Handler                                        │
│  - Business Logic                                            │
│  - Database Operations                                       │
│  - AI Pipeline Orchestrator                                  │
└────────────┬───────────────────────┬────────────────────────┘
             │                       │
             │                       │
    ┌────────▼────────┐    ┌────────▼─────────────────────┐
    │   DATABASE      │    │    AI PIPELINE               │
    │   MySQL         │    │  - Video Processing          │
    │   - bills       │    │  - Roboflow Detection        │
    │   - reconcile   │    │  - OpenCV Tracking           │
    │   - alerts      │    │  - Bag Counting              │
    └─────────────────┘    └──────────────────────────────┘
```

### Component Responsibilities

**Frontend**: User interface for data entry, video upload, and viewing results

**Backend**: API server, business logic, database operations, AI pipeline coordination

**Database**: Persistent storage for bills, verification results, and fraud alerts

**AI Pipeline**: Video processing, bag detection, and unique bag counting


## 2. System Flow

### 2.1 Bill Registration Flow

```
User → Fill Form → Submit → Backend validates → Insert into bills table
                                                 (status = PENDING)
                                              → Return success → Show confirmation
```

Step-by-step:
1. User opens Bill Registration page
2. User fills in: bill_no, bill_date, farmer_id, trader_id, mill_id, vehicle_no, manual_bag_count, manual_total_weight, net_weight_per_bag
3. User clicks Submit
4. Frontend sends POST request to `/api/bills`
5. Backend validates all fields
6. Backend inserts record into `bills` table with status = PENDING
7. Backend returns success response with bill_id
8. Frontend shows success message

### 2.2 AI Verification Flow

```
User → Select PENDING bill → Upload video → Backend processes video
                                          → Extract frames
                                          → Roboflow detection
                                          → OpenCV tracking
                                          → Count unique bags
                                          → Compare counts
                                          → Update bill status
                                          → Create reconciliation record
                                          → [If mismatch] Create fraud alert
                                          → Return result → Show verification result
```

Step-by-step:
1. User opens AI Verification page
2. System loads all bills with status = PENDING
3. User selects a bill from the list
4. User uploads entry video file
5. User clicks "Run Verification"
6. Frontend sends POST request to `/api/ai/verify` with bill_id and video file
7. Backend saves video to temporary location
8. Backend runs AI pipeline:
   - Extract frames from video (skip frames for performance)
   - Send frames to Roboflow workflow for bag detection
   - Extract bounding boxes from Roboflow response
   - Track unique bags using center distance matching
   - Calculate final AI bag count
9. Backend compares AI count with manual count from bill
10. If counts match (difference = 0):
    - Update bill status to VERIFIED
    - Create reconciliation record
11. If counts don't match (difference ≠ 0):
    - Update bill status to FRAUD
    - Create reconciliation record
    - Create fraud alert with severity based on difference
12. Backend returns verification result
13. Frontend displays result with manual count, AI count, and difference

### 2.3 Fraud Alert Flow

```
Fraud detected → Create alert record → Store in fraud_alerts table
                                    → Show in Fraud Alerts page
                                    → User clicks row → Expand to show details
```

Step-by-step:
1. When verification detects mismatch, fraud alert is created
2. Alert includes: bill_id, severity, message, manual_bag_count, ai_bag_count, difference
3. User navigates to Fraud Alerts page
4. System loads all fraud alerts
5. User clicks on a fraud alert row
6. Row expands to show full bill details below the selected row
7. Details include: bill_no, farmer_id, trader_id, mill_id, vehicle_no, counts, difference


## 3. Database Design

### 3.1 Schema Overview

```
bills (1) ──────< (N) reconciliation
  │
  └──────────────< (N) fraud_alerts
```

### 3.2 Tables

#### bills

Primary table storing procurement bill information.

```sql
CREATE TABLE bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_no VARCHAR(50) UNIQUE NOT NULL,
    bill_date DATE NOT NULL,
    farmer_id VARCHAR(50) NOT NULL,
    trader_id VARCHAR(50) NOT NULL,
    mill_id VARCHAR(50) NOT NULL,
    vehicle_no VARCHAR(20) NOT NULL,
    manual_bag_count INT NOT NULL,
    manual_total_weight DECIMAL(10,2) NOT NULL,
    net_weight_per_bag DECIMAL(10,2) NOT NULL,
    status ENUM('PENDING', 'VERIFIED', 'FRAUD') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_bill_no (bill_no)
);
```

Key columns:
- `bill_id`: Auto-increment primary key
- `bill_no`: Unique bill identifier (business key)
- `status`: Current verification status
- `manual_bag_count`: Count reported in manual bill (used for comparison)

#### reconciliation

Stores AI verification results and comparison data.

```sql
CREATE TABLE reconciliation (
    reconciliation_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    manual_bag_count INT NOT NULL,
    ai_bag_count INT NOT NULL,
    difference INT NOT NULL,
    video_path VARCHAR(255),
    verification_status ENUM('VERIFIED', 'FRAUD') NOT NULL,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    INDEX idx_bill_id (bill_id),
    INDEX idx_verification_status (verification_status)
);
```

Key columns:
- `bill_id`: Foreign key to bills table
- `manual_bag_count`: Copy from bills table for historical record
- `ai_bag_count`: Count detected by AI pipeline
- `difference`: Calculated as (manual_bag_count - ai_bag_count)
- `verification_status`: Result of comparison

#### fraud_alerts

Stores fraud detection alerts for mismatched counts.

```sql
CREATE TABLE fraud_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    message TEXT NOT NULL,
    manual_bag_count INT NOT NULL,
    ai_bag_count INT NOT NULL,
    difference INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    INDEX idx_bill_id (bill_id),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at)
);
```

Key columns:
- `bill_id`: Foreign key to bills table
- `severity`: Calculated based on difference magnitude
  - LOW: difference 1-2 bags
  - MEDIUM: difference 3-5 bags
  - HIGH: difference > 5 bags
- `message`: Human-readable fraud description
- `difference`: Absolute difference between counts


## 4. API Design

### 4.1 POST /api/bills

Create a new procurement bill.

**Request:**
```json
{
  "bill_no": "BILL-2026-001",
  "bill_date": "2026-02-15",
  "farmer_id": "F12345",
  "trader_id": "T67890",
  "mill_id": "M11111",
  "vehicle_no": "KA01AB1234",
  "manual_bag_count": 50,
  "manual_total_weight": 2500.00,
  "net_weight_per_bag": 50.00
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Bill created successfully",
  "data": {
    "bill_id": 1,
    "bill_no": "BILL-2026-001",
    "status": "PENDING",
    "created_at": "2026-02-15T10:30:00"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Bill number already exists"
}
```

### 4.2 GET /api/bills

Retrieve all bills or filter by status.

**Request:**
```
GET /api/bills?status=PENDING
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "bill_id": 1,
      "bill_no": "BILL-2026-001",
      "bill_date": "2026-02-15",
      "farmer_id": "F12345",
      "trader_id": "T67890",
      "mill_id": "M11111",
      "vehicle_no": "KA01AB1234",
      "manual_bag_count": 50,
      "manual_total_weight": 2500.00,
      "net_weight_per_bag": 50.00,
      "status": "PENDING",
      "created_at": "2026-02-15T10:30:00"
    }
  ]
}
```

### 4.3 POST /api/ai/verify

Process video and verify bag count.

**Request:**
```
Content-Type: multipart/form-data

bill_id: 1
video: [binary file data]
```

**Response (200 OK - Verified):**
```json
{
  "success": true,
  "message": "Verification completed - Counts match",
  "data": {
    "bill_id": 1,
    "bill_no": "BILL-2026-001",
    "manual_bag_count": 50,
    "ai_bag_count": 50,
    "difference": 0,
    "status": "VERIFIED",
    "verified_at": "2026-02-15T11:00:00"
  }
}
```

**Response (200 OK - Fraud Detected):**
```json
{
  "success": true,
  "message": "Verification completed - Fraud detected",
  "data": {
    "bill_id": 1,
    "bill_no": "BILL-2026-001",
    "manual_bag_count": 50,
    "ai_bag_count": 45,
    "difference": 5,
    "status": "FRAUD",
    "verified_at": "2026-02-15T11:00:00",
    "fraud_alert": {
      "alert_id": 1,
      "severity": "MEDIUM",
      "message": "Manual count exceeds AI count by 5 bags"
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid video format. Only MP4, AVI, MOV allowed"
}
```

### 4.4 GET /api/verified-bills

Retrieve all verified bills with reconciliation data.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "bill_id": 1,
      "bill_no": "BILL-2026-001",
      "vehicle_no": "KA01AB1234",
      "manual_bag_count": 50,
      "ai_bag_count": 50,
      "difference": 0,
      "verified_at": "2026-02-15T11:00:00"
    }
  ]
}
```

### 4.5 GET /api/fraud-alerts

Retrieve all fraud alerts with bill details.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "alert_id": 1,
      "bill_id": 2,
      "bill_no": "BILL-2026-002",
      "severity": "HIGH",
      "message": "Manual count exceeds AI count by 8 bags",
      "manual_bag_count": 60,
      "ai_bag_count": 52,
      "difference": 8,
      "created_at": "2026-02-15T12:00:00",
      "bill_details": {
        "farmer_id": "F54321",
        "trader_id": "T09876",
        "mill_id": "M22222",
        "vehicle_no": "KA02CD5678"
      }
    }
  ]
}
```

### 4.6 GET /api/all-records

Retrieve combined view of all bills with verification status.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "bill_id": 1,
      "bill_no": "BILL-2026-001",
      "bill_date": "2026-02-15",
      "farmer_id": "F12345",
      "trader_id": "T67890",
      "mill_id": "M11111",
      "vehicle_no": "KA01AB1234",
      "manual_bag_count": 50,
      "manual_total_weight": 2500.00,
      "status": "VERIFIED",
      "ai_bag_count": 50,
      "difference": 0,
      "verified_at": "2026-02-15T11:00:00"
    },
    {
      "bill_id": 2,
      "bill_no": "BILL-2026-002",
      "bill_date": "2026-02-15",
      "farmer_id": "F54321",
      "trader_id": "T09876",
      "mill_id": "M22222",
      "vehicle_no": "KA02CD5678",
      "manual_bag_count": 60,
      "manual_total_weight": 3000.00,
      "status": "FRAUD",
      "ai_bag_count": 52,
      "difference": 8,
      "verified_at": "2026-02-15T12:00:00"
    },
    {
      "bill_id": 3,
      "bill_no": "BILL-2026-003",
      "bill_date": "2026-02-15",
      "farmer_id": "F99999",
      "trader_id": "T11111",
      "mill_id": "M33333",
      "vehicle_no": "KA03EF9012",
      "manual_bag_count": 40,
      "manual_total_weight": 2000.00,
      "status": "PENDING",
      "ai_bag_count": null,
      "difference": null,
      "verified_at": null
    }
  ]
}
```


## 5. AI Pipeline Design

### 5.1 Pipeline Overview

```
Video File → Frame Extraction → Frame Skipping → Roboflow Detection
                                                → Bounding Boxes
                                                → Unique Bag Tracking
                                                → Final Count
```

### 5.2 Detailed Pipeline Steps

#### Step 1: Video Frame Extraction

Use OpenCV to read video and extract frames.

```python
import cv2

def extract_frames(video_path, frame_skip=5, max_frames=100):
    """
    Extract frames from video with skipping for performance
    
    Args:
        video_path: Path to uploaded video
        frame_skip: Process every Nth frame (default 5)
        max_frames: Maximum frames to process (default 100)
    
    Returns:
        List of frame images
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0
    processed_count = 0
    
    while cap.isOpened() and processed_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for performance
        if frame_count % frame_skip == 0:
            frames.append(frame)
            processed_count += 1
        
        frame_count += 1
    
    cap.release()
    return frames
```

**Configuration:**
- `frame_skip = 5`: Process every 5th frame (reduces processing time)
- `max_frames = 100`: Limit total frames processed (prevents timeout)
- For 30 FPS video: 100 frames = ~16 seconds of video coverage

#### Step 2: Roboflow Workflow Inference

Send frames to Roboflow API for bag detection.

```python
from roboflow import Roboflow

def detect_bags_in_frames(frames, api_key, workspace, workflow_id):
    """
    Run Roboflow workflow on frames to detect bags
    
    Args:
        frames: List of frame images
        api_key: Roboflow API key
        workspace: Roboflow workspace name
        workflow_id: Roboflow workflow ID
    
    Returns:
        List of detection results per frame
    """
    rf = Roboflow(api_key=api_key)
    workflow = rf.workspace(workspace).workflow(workflow_id)
    
    all_detections = []
    
    for frame in frames:
        # Convert frame to format Roboflow expects
        result = workflow.predict(frame)
        
        # Extract bounding boxes from result
        detections = extract_bounding_boxes(result)
        all_detections.append(detections)
    
    return all_detections
```

**Roboflow Response Format:**
```json
{
  "predictions": [
    {
      "x": 320,
      "y": 240,
      "width": 80,
      "height": 100,
      "confidence": 0.95,
      "class": "bag"
    }
  ]
}
```

#### Step 3: Bounding Box Extraction

Extract bag coordinates from Roboflow response.

```python
def extract_bounding_boxes(roboflow_result):
    """
    Extract bounding box coordinates from Roboflow result
    
    Returns:
        List of (center_x, center_y, width, height, confidence)
    """
    boxes = []
    
    if 'predictions' in roboflow_result:
        for pred in roboflow_result['predictions']:
            if pred['class'] == 'bag' and pred['confidence'] > 0.7:
                center_x = pred['x']
                center_y = pred['y']
                width = pred['width']
                height = pred['height']
                confidence = pred['confidence']
                
                boxes.append({
                    'center_x': center_x,
                    'center_y': center_y,
                    'width': width,
                    'height': height,
                    'confidence': confidence
                })
    
    return boxes
```

**Confidence Threshold:** Only consider detections with confidence > 0.7

#### Step 4: Unique Bag Tracking

Track unique bags across frames using center distance matching.

```python
import math

def count_unique_bags(all_frame_detections, distance_threshold=50):
    """
    Count unique bags across all frames using center distance matching
    
    Args:
        all_frame_detections: List of detections per frame
        distance_threshold: Max distance (pixels) to consider same bag
    
    Returns:
        Final unique bag count
    """
    unique_bags = []
    
    for frame_detections in all_frame_detections:
        for detection in frame_detections:
            center = (detection['center_x'], detection['center_y'])
            
            # Check if this bag matches any existing unique bag
            is_new_bag = True
            
            for unique_bag in unique_bags:
                distance = calculate_distance(center, unique_bag['center'])
                
                if distance < distance_threshold:
                    # Same bag detected again, update position
                    unique_bag['center'] = center
                    unique_bag['count'] += 1
                    is_new_bag = False
                    break
            
            if is_new_bag:
                # New unique bag found
                unique_bags.append({
                    'center': center,
                    'count': 1,
                    'first_seen': len(unique_bags)
                })
    
    # Filter out bags seen in very few frames (noise)
    min_appearances = 2
    confirmed_bags = [bag for bag in unique_bags if bag['count'] >= min_appearances]
    
    return len(confirmed_bags)

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
```

**Tracking Logic:**
- Compare each detected bag center with existing unique bags
- If distance < threshold (50 pixels), consider it the same bag
- If distance >= threshold, consider it a new unique bag
- Filter bags that appear in < 2 frames (reduces false positives)

**Distance Threshold:** 50 pixels works for typical vehicle entry videos

#### Step 5: Final Count Output

```python
def run_ai_verification(video_path):
    """
    Complete AI pipeline to count bags in video
    
    Returns:
        ai_bag_count (integer)
    """
    # Step 1: Extract frames
    frames = extract_frames(video_path, frame_skip=5, max_frames=100)
    
    # Step 2: Run Roboflow detection
    all_detections = detect_bags_in_frames(
        frames,
        api_key=ROBOFLOW_API_KEY,
        workspace=ROBOFLOW_WORKSPACE,
        workflow_id=ROBOFLOW_WORKFLOW_ID
    )
    
    # Step 3: Count unique bags
    ai_bag_count = count_unique_bags(all_detections, distance_threshold=50)
    
    return ai_bag_count
```

### 5.3 Performance Optimizations

- **Frame Skipping:** Process every 5th frame instead of all frames
- **Max Frames Limit:** Cap at 100 frames to prevent timeout
- **Confidence Filtering:** Only process high-confidence detections (> 0.7)
- **Appearance Filtering:** Require bags to appear in at least 2 frames

### 5.4 AI Pipeline Configuration

```python
# config.py
AI_CONFIG = {
    'frame_skip': 5,              # Process every 5th frame
    'max_frames': 100,            # Maximum frames to process
    'confidence_threshold': 0.7,  # Minimum detection confidence
    'distance_threshold': 50,     # Pixels for same bag matching
    'min_appearances': 2,         # Minimum frames bag must appear
    'video_timeout': 60           # Seconds before timeout
}
```


## 6. UI Design Overview

### 6.1 Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         HEADER                               │
│              Rice Mill AI - Bag Verification                 │
└─────────────────────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────────────────────┐
│          │                                                   │
│ SIDEBAR  │              MAIN CONTENT AREA                    │
│          │                                                   │
│ - Home   │  [Dynamic content based on selected page]        │
│ - Bill   │                                                   │
│   Reg    │                                                   │
│ - AI     │                                                   │
│   Verify │                                                   │
│ - Verify │                                                   │
│   Bills  │                                                   │
│ - Fraud  │                                                   │
│   Alerts │                                                   │
│ - All    │                                                   │
│   Record │                                                   │
│          │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

### 6.2 Page Designs

#### 6.2.1 Bill Registration Page

Form layout with input fields:

```
┌─────────────────────────────────────────────────────────────┐
│  Register New Bill                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Bill Number:        [________________]                      │
│  Bill Date:          [________________]  (date picker)       │
│  Farmer ID:          [________________]                      │
│  Trader ID:          [________________]                      │
│  Mill ID:            [________________]                      │
│  Vehicle Number:     [________________]                      │
│  Manual Bag Count:   [________________]  (number)            │
│  Manual Total Weight:[________________]  (kg)                │
│  Net Weight/Bag:     [________________]  (kg)                │
│                                                              │
│                      [Submit Bill]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Input validation on all fields
- Date picker for bill_date
- Number inputs for counts and weights
- Success/error message display after submission
- Clear form after successful submission

#### 6.2.2 AI Verification Page

Two-panel layout:

```
┌─────────────────────────────────────────────────────────────┐
│  AI Bag Count Verification                                   │
├──────────────────────────┬──────────────────────────────────┤
│ PENDING BILLS            │  VERIFICATION PANEL              │
│                          │                                  │
│ ┌──────────────────────┐ │  Selected Bill: BILL-2026-001   │
│ │ BILL-2026-001        │ │  Manual Count: 50 bags          │
│ │ Vehicle: KA01AB1234  │ │                                  │
│ │ Count: 50 bags       │ │  Upload Entry Video:            │
│ │ [Select]             │ │  [Choose File] video.mp4        │
│ └──────────────────────┘ │                                  │
│                          │  [Run AI Verification]           │
│ ┌──────────────────────┐ │                                  │
│ │ BILL-2026-003        │ │  ─────────────────────────────  │
│ │ Vehicle: KA03EF9012  │ │  Processing... 45%              │
│ │ Count: 40 bags       │ │  [████████░░░░░░░░░░]           │
│ │ [Select]             │ │                                  │
│ └──────────────────────┘ │  ─────────────────────────────  │
│                          │                                  │
│                          │  RESULT:                         │
│                          │  ✓ Verification Complete         │
│                          │  Manual Count: 50                │
│                          │  AI Count: 50                    │
│                          │  Difference: 0                   │
│                          │  Status: VERIFIED                │
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

**Features:**
- Left panel: List of PENDING bills (scrollable)
- Right panel: Verification interface
- File upload with format validation
- Progress bar during AI processing
- Result display with color coding (green for verified, red for fraud)

#### 6.2.3 Verified Bills Page

Table view:

```
┌─────────────────────────────────────────────────────────────┐
│  Verified Bills                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Bill No  │ Vehicle   │ Manual │ AI  │ Diff │ Time    │  │
│  ├──────────┼───────────┼────────┼─────┼──────┼─────────┤  │
│  │ BILL-001 │ KA01AB123 │   50   │ 50  │  0   │ 11:00AM │  │
│  │ BILL-004 │ KA04GH345 │   45   │ 45  │  0   │ 01:30PM │  │
│  │ BILL-007 │ KA07KL678 │   60   │ 60  │  0   │ 03:15PM │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Sortable columns
- Search/filter by bill number or vehicle
- Pagination for large datasets
- Export to CSV option (future)

#### 6.2.4 Fraud Alerts Page

Expandable table view:

```
┌─────────────────────────────────────────────────────────────┐
│  Fraud Alerts                                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Severity │ Message              │ Diff │ Time        │  │
│  ├──────────┼──────────────────────┼──────┼─────────────┤  │
│  │ 🔴 HIGH  │ Count mismatch: 8... │  +8  │ 12:00PM  [▼]│  │
│  ├──────────┴──────────────────────┴──────┴─────────────┤  │
│  │ EXPANDED DETAILS:                                     │  │
│  │ Bill No: BILL-2026-002                                │  │
│  │ Farmer ID: F54321                                     │  │
│  │ Trader ID: T09876                                     │  │
│  │ Mill ID: M22222                                       │  │
│  │ Vehicle: KA02CD5678                                   │  │
│  │ Manual Count: 60 bags                                 │  │
│  │ AI Count: 52 bags                                     │  │
│  │ Difference: +8 bags (manual exceeds AI)               │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🟡 MEDIUM│ Count mismatch: 4... │  +4  │ 02:30PM  [▶]│  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Color-coded severity (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW)
- Click row to expand/collapse details
- Details appear directly below clicked row
- Smooth expand/collapse animation
- Sort by severity or time

**Expand Behavior:**
1. User clicks on fraud alert row
2. Row expands with smooth animation
3. Full bill details appear below the row
4. Click again to collapse
5. Only one row expanded at a time

#### 6.2.5 All Records Page

Combined table view with status filter:

```
┌─────────────────────────────────────────────────────────────┐
│  All Records                                                 │
├─────────────────────────────────────────────────────────────┤
│  Filter: [All ▼] [PENDING] [VERIFIED] [FRAUD]              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Bill  │ Date  │ Vehicle │ Manual │ AI │ Diff │ Status │  │
│  ├───────┼───────┼─────────┼────────┼────┼──────┼────────┤  │
│  │ 001   │ 02/15 │ KA01... │   50   │ 50 │  0   │ ✓ VER  │  │
│  │ 002   │ 02/15 │ KA02... │   60   │ 52 │ +8   │ ✗ FRD  │  │
│  │ 003   │ 02/15 │ KA03... │   40   │ -  │  -   │ ⏳ PND │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Status filter buttons
- Color-coded status indicators
- Shows all bill data in one view
- Sortable by any column
- Search functionality

### 6.3 Color Scheme

```
Primary Colors:
- Header: #2c3e50 (dark blue-gray)
- Sidebar: #34495e (medium blue-gray)
- Main: #ecf0f1 (light gray)

Status Colors:
- VERIFIED: #27ae60 (green)
- FRAUD: #e74c3c (red)
- PENDING: #f39c12 (orange)

Severity Colors:
- HIGH: #e74c3c (red)
- MEDIUM: #f39c12 (orange)
- LOW: #f1c40f (yellow)
```

### 6.4 Responsive Design

- Desktop: Full sidebar + main content
- Tablet: Collapsible sidebar
- Mobile: Hamburger menu (out of scope for hackathon)


## 7. Error Handling and Edge Cases

### 7.1 Input Validation Errors

**Bill Registration:**
- Empty required fields → Show "All fields are required" error
- Duplicate bill_no → Show "Bill number already exists" error
- Invalid date format → Show "Invalid date format" error
- Negative bag count → Show "Bag count must be positive" error
- Invalid weight values → Show "Weight must be a positive number" error

**AI Verification:**
- No bill selected → Show "Please select a bill first" error
- No video uploaded → Show "Please upload a video file" error
- Invalid video format → Show "Only MP4, AVI, MOV formats allowed" error
- File size > 100MB → Show "Video file too large (max 100MB)" error
- Bill already verified → Show "Bill already verified, cannot re-verify" error

### 7.2 AI Pipeline Errors

**Video Processing Errors:**
- Corrupted video file → Return error "Unable to read video file"
- Video too short (< 5 seconds) → Return error "Video too short for analysis"
- No frames extracted → Return error "Failed to extract frames from video"

**Roboflow API Errors:**
- API key invalid → Return error "Roboflow authentication failed"
- API rate limit exceeded → Return error "API rate limit exceeded, try again later"
- Network timeout → Return error "Connection to Roboflow failed"
- No bags detected → Return warning "No bags detected in video, AI count = 0"

**Bag Counting Edge Cases:**
- Zero bags detected → Set ai_bag_count = 0, compare with manual count
- Very high bag count (> 200) → Log warning, proceed with count
- Low confidence detections → Filter out detections with confidence < 0.7
- Overlapping bags → Distance threshold handles this, count as separate if centers far apart

### 7.3 Database Errors

**Connection Errors:**
- Database unavailable → Return 500 error "Database connection failed"
- Query timeout → Return 500 error "Database query timeout"

**Constraint Violations:**
- Foreign key violation → Return 400 error "Invalid bill_id reference"
- Unique constraint violation → Return 400 error "Duplicate entry"

**Transaction Errors:**
- Rollback on failure → Ensure bill status not updated if reconciliation insert fails
- Atomic operations → Update bill status and create reconciliation in same transaction

### 7.4 File Upload Errors

**Storage Errors:**
- Disk full → Return 500 error "Unable to save video file"
- Permission denied → Return 500 error "File system permission error"
- Invalid path → Return 500 error "Invalid file path"

**Cleanup:**
- Delete temporary video files after processing
- Clean up failed uploads
- Implement file retention policy (delete videos after 30 days)

### 7.5 Timeout Handling

**Video Processing Timeout:**
- Set timeout to 60 seconds
- If processing exceeds timeout → Cancel operation, return error
- Show timeout error to user: "Video processing timeout, try shorter video"

**API Request Timeout:**
- Set timeout to 30 seconds for Roboflow API calls
- Retry once on timeout
- If retry fails → Return error to user

### 7.6 Edge Case Scenarios

**Scenario 1: Manual count = 0**
- Allow registration with 0 bags
- AI verification should also detect 0 bags
- If AI detects bags when manual = 0 → Flag as fraud

**Scenario 2: Very large difference (> 20 bags)**
- Set severity to HIGH
- Log for manual review
- Consider video quality issue

**Scenario 3: Multiple bills for same vehicle**
- Allow multiple bills per vehicle (different dates)
- Each bill is independent verification

**Scenario 4: Video shows multiple vehicles**
- Current design assumes one vehicle per video
- Future: Add vehicle detection and isolation

**Scenario 5: Poor video quality**
- Low resolution → May reduce detection accuracy
- Dark lighting → May miss bags
- Recommendation: Require minimum video quality standards

**Scenario 6: Bags partially visible**
- Roboflow may detect partial bags
- Confidence threshold (0.7) helps filter uncertain detections
- Distance threshold prevents counting same bag multiple times


## 8. Security Considerations

### 8.1 API Key Safety

**Roboflow API Key Protection:**
- Store API key in environment variables, never in code
- Use `.env` file for local development
- Add `.env` to `.gitignore` to prevent committing
- Access via `os.getenv('ROBOFLOW_API_KEY')`

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

ROBOFLOW_API_KEY = os.getenv('ROBOFLOW_API_KEY')
ROBOFLOW_WORKSPACE = os.getenv('ROBOFLOW_WORKSPACE')
ROBOFLOW_WORKFLOW_ID = os.getenv('ROBOFLOW_WORKFLOW_ID')
```

**Database Credentials:**
- Store MySQL credentials in environment variables
- Never hardcode passwords in source code
- Use connection pooling for security and performance

```python
# database.py
import os
import mysql.connector

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'rice_mill_ai')
}
```

### 8.2 File Upload Validation

**File Type Validation:**
- Check file extension: only allow .mp4, .avi, .mov
- Verify MIME type matches extension
- Reject executable files and scripts

```python
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
ALLOWED_MIME_TYPES = {'video/mp4', 'video/x-msvideo', 'video/quicktime'}

def validate_video_file(file):
    # Check extension
    if not file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        return False, "Invalid file extension"
    
    # Check MIME type
    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, "Invalid file type"
    
    # Check file size (100MB max)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 100 * 1024 * 1024:
        return False, "File too large"
    
    return True, "Valid"
```

**File Storage Security:**
- Store uploaded videos outside web root
- Use random filenames to prevent path traversal
- Set restrictive file permissions (read-only for web server)

```python
import uuid
import os

UPLOAD_FOLDER = '/var/uploads/videos'  # Outside web root

def save_video_securely(file):
    # Generate random filename
    random_name = str(uuid.uuid4())
    extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{random_name}.{extension}"
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Set restrictive permissions
    os.chmod(filepath, 0o644)
    
    return filepath
```

### 8.3 SQL Injection Prevention

**Use Parameterized Queries:**
- Never concatenate user input into SQL strings
- Always use parameterized queries with placeholders

```python
# BAD - Vulnerable to SQL injection
query = f"SELECT * FROM bills WHERE bill_no = '{bill_no}'"

# GOOD - Safe parameterized query
query = "SELECT * FROM bills WHERE bill_no = %s"
cursor.execute(query, (bill_no,))
```

**Input Sanitization:**
- Validate all user inputs before database operations
- Use type checking (int for counts, decimal for weights)
- Limit string lengths to prevent buffer overflow

### 8.4 Cross-Site Scripting (XSS) Prevention

**Output Encoding:**
- Escape HTML special characters in user input before display
- Use JavaScript's `textContent` instead of `innerHTML` for user data

```javascript
// BAD - Vulnerable to XSS
element.innerHTML = userInput;

// GOOD - Safe from XSS
element.textContent = userInput;
```

**Content Security Policy:**
- Add CSP header to prevent inline script execution
- Only allow scripts from same origin

```python
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
```

### 8.5 Access Control

**For Hackathon Prototype:**
- No authentication required (single user assumption)
- All endpoints publicly accessible

**For Production (Future):**
- Implement user authentication (login/logout)
- Role-based access control (admin, operator, viewer)
- Session management with secure cookies
- JWT tokens for API authentication

### 8.6 Data Privacy

**Sensitive Data Handling:**
- Farmer IDs, Trader IDs are sensitive
- For demo, use anonymized IDs (F12345, T67890)
- In production, implement data encryption at rest

**Video Data:**
- Videos may contain identifiable information
- Implement retention policy (delete after 30 days)
- Secure deletion (overwrite before delete)

### 8.7 Rate Limiting

**API Rate Limiting:**
- Limit video upload requests to prevent abuse
- Max 10 verifications per minute per IP
- Return 429 Too Many Requests if exceeded

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/ai/verify', methods=['POST'])
@limiter.limit("10 per minute")
def verify_bill():
    # Verification logic
    pass
```

### 8.8 Error Message Security

**Don't Expose Internal Details:**
- Generic error messages for users
- Detailed errors only in server logs
- Never expose database structure or file paths

```python
# BAD - Exposes internal details
return {"error": "MySQL error: Table 'bills' doesn't exist at /var/lib/mysql"}

# GOOD - Generic message
return {"error": "Database error occurred"}
# Log detailed error server-side
logger.error(f"MySQL error: {str(e)}")
```


## 9. Performance Considerations

### 9.1 Video Processing Optimization

**Frame Skipping Strategy:**
- Process every 5th frame instead of all frames
- Reduces processing time by 80%
- Still captures sufficient bag information
- For 30 FPS video: 6 frames per second analyzed

**Frame Limit:**
- Cap at 100 frames maximum
- Prevents timeout on long videos
- 100 frames at 6 FPS = ~16 seconds coverage
- Sufficient for typical vehicle entry videos

**Parallel Processing (Future):**
- Process multiple frames concurrently
- Use multiprocessing or threading
- Can reduce processing time by 50%

### 9.2 Database Performance

**Indexing Strategy:**
```sql
-- Index on frequently queried columns
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_bill_no ON bills(bill_no);
CREATE INDEX idx_reconciliation_bill_id ON reconciliation(bill_id);
CREATE INDEX idx_fraud_alerts_bill_id ON fraud_alerts(bill_id);
CREATE INDEX idx_fraud_alerts_severity ON fraud_alerts(severity);
CREATE INDEX idx_fraud_alerts_created_at ON fraud_alerts(created_at);
```

**Query Optimization:**
- Use JOIN instead of multiple queries
- Limit result sets with pagination
- Use SELECT specific columns instead of SELECT *

```python
# Optimized query for all records
query = """
    SELECT 
        b.bill_id, b.bill_no, b.bill_date, b.vehicle_no, 
        b.manual_bag_count, b.status,
        r.ai_bag_count, r.difference, r.verified_at
    FROM bills b
    LEFT JOIN reconciliation r ON b.bill_id = r.bill_id
    ORDER BY b.created_at DESC
    LIMIT 100
"""
```

**Connection Pooling:**
- Reuse database connections
- Reduce connection overhead
- Configure pool size based on expected load

```python
from mysql.connector import pooling

connection_pool = pooling.MySQLConnectionPool(
    pool_name="rice_mill_pool",
    pool_size=5,
    **DB_CONFIG
)
```

### 9.3 API Response Time

**Target Response Times:**
- GET endpoints: < 500ms
- POST /api/bills: < 200ms
- POST /api/ai/verify: < 60 seconds (video processing)

**Caching Strategy (Future):**
- Cache verified bills list for 5 minutes
- Cache fraud alerts list for 5 minutes
- Invalidate cache on new verification

**Pagination:**
- Limit results to 50 records per page
- Implement offset-based pagination
- Add page parameter to GET endpoints

```python
@app.route('/api/verified-bills')
def get_verified_bills():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    query = """
        SELECT * FROM bills 
        WHERE status = 'VERIFIED'
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (per_page, offset))
```

### 9.4 Frontend Performance

**Lazy Loading:**
- Load bill lists on demand
- Don't load all records at once
- Implement infinite scroll or pagination

**Debouncing:**
- Debounce search input (wait 300ms after typing)
- Prevents excessive API calls

```javascript
let searchTimeout;
function handleSearch(query) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        fetchBills(query);
    }, 300);
}
```

**Minimize DOM Updates:**
- Batch DOM updates
- Use document fragments for multiple insertions
- Update only changed elements

### 9.5 File Storage Optimization

**Video Storage:**
- Store videos on disk, not in database
- Store only file path in database
- Implement cleanup job to delete old videos

**Disk Space Management:**
- Monitor available disk space
- Alert when space < 10GB
- Automatic cleanup of videos > 30 days old

```python
import os
import time

def cleanup_old_videos(days=30):
    """Delete videos older than specified days"""
    cutoff_time = time.time() - (days * 86400)
    
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.getmtime(filepath) < cutoff_time:
            os.remove(filepath)
```

### 9.6 Roboflow API Optimization

**Batch Processing:**
- Send multiple frames in single API call if supported
- Reduces API call overhead

**Request Timeout:**
- Set timeout to 30 seconds per API call
- Retry once on timeout
- Fail gracefully if retry fails

**API Call Reduction:**
- Skip frames with no motion (future enhancement)
- Use frame differencing to detect static frames

### 9.7 Memory Management

**Video Processing Memory:**
- Process frames in batches
- Release frame memory after processing
- Don't load entire video into memory

```python
def extract_frames_memory_efficient(video_path):
    cap = cv2.VideoCapture(video_path)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame immediately
        process_frame(frame)
        
        # Release frame memory
        del frame
    
    cap.release()
```

**Database Result Sets:**
- Use cursor.fetchmany() instead of fetchall()
- Process results in chunks
- Close cursors after use

### 9.8 Monitoring and Metrics

**Key Metrics to Track:**
- Average video processing time
- API response times
- Database query times
- Error rates
- Disk space usage
- API call count (Roboflow)

**Logging:**
- Log all API requests with timestamps
- Log processing times for optimization
- Log errors with stack traces

```python
import logging
import time

logger = logging.getLogger(__name__)

def log_processing_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} took {end_time - start_time:.2f}s")
        return result
    return wrapper

@log_processing_time
def run_ai_verification(video_path):
    # Processing logic
    pass
```


## 10. Future Improvements

### 10.1 Authentication and Authorization

**User Management:**
- Implement login/logout functionality
- Role-based access control:
  - Admin: Full access to all features
  - Operator: Can register bills and run verification
  - Viewer: Read-only access to reports
- Session management with secure cookies
- Password hashing with bcrypt

**Multi-tenant Support:**
- Support multiple rice mills
- Isolate data by mill_id
- Mill-specific dashboards

### 10.2 Advanced AI Features

**Multi-Camera Support:**
- Process videos from multiple angles
- Combine detections from all cameras
- Improve accuracy with triangulation

**Vehicle Detection:**
- Detect and isolate vehicle in frame
- Focus bag detection on vehicle area only
- Handle multiple vehicles in same video

**Bag Type Classification:**
- Classify bags by size (small, medium, large)
- Detect bag condition (torn, intact)
- Identify bag material (jute, plastic)

**Motion Detection:**
- Skip frames with no motion
- Reduce processing time by 50%
- Focus on frames where bags are visible

**Real-time Processing:**
- Process video stream in real-time
- Live bag counting during vehicle entry
- Immediate fraud detection

### 10.3 Enhanced Reporting

**Dashboard:**
- Summary statistics (total bills, verified, fraud rate)
- Charts and graphs (daily trends, fraud by mill)
- Real-time updates using WebSockets

**Analytics:**
- Fraud pattern analysis
- Identify high-risk traders/mills
- Seasonal trends in fraud attempts

**Export Features:**
- Export reports to PDF
- Export data to Excel/CSV
- Scheduled email reports

**Audit Trail:**
- Track all user actions
- Log all bill modifications
- Maintain complete history

### 10.4 Mobile Application

**Mobile App Features:**
- Capture video directly from phone camera
- Upload and verify on-the-go
- Push notifications for fraud alerts
- Offline mode with sync

**Progressive Web App (PWA):**
- Install as mobile app
- Offline functionality
- Camera access from browser

### 10.5 Integration Capabilities

**Government Systems Integration:**
- Connect to central procurement database
- Sync farmer/trader information
- Automated payment processing

**SMS/Email Alerts:**
- Send fraud alerts via SMS
- Email reports to supervisors
- Notify farmers of verification status

**Webhook Support:**
- Trigger external systems on fraud detection
- Real-time data sync with other applications

### 10.6 Performance Enhancements

**GPU Acceleration:**
- Use GPU for video processing
- Faster frame extraction and analysis
- Reduce processing time to < 10 seconds

**Distributed Processing:**
- Queue-based architecture (Celery + Redis)
- Process multiple videos in parallel
- Scale horizontally with worker nodes

**Edge Computing:**
- Deploy AI model on edge devices
- Process videos locally at mill
- Reduce bandwidth and latency

### 10.7 Data Management

**Data Backup:**
- Automated daily database backups
- Video archive to cloud storage
- Disaster recovery plan

**Data Retention Policy:**
- Archive old bills (> 1 year)
- Compress archived videos
- Purge data after retention period

**Data Migration:**
- Import historical bills from Excel
- Bulk upload functionality
- Data validation during import

### 10.8 User Experience Improvements

**Video Preview:**
- Show video thumbnail before upload
- Preview video with detected bags highlighted
- Playback with bounding boxes overlay

**Bulk Operations:**
- Verify multiple bills at once
- Batch video upload
- Bulk status updates

**Advanced Search:**
- Search by date range
- Filter by farmer/trader/mill
- Full-text search on all fields

**Notifications:**
- In-app notification system
- Alert badges for new fraud cases
- Toast messages for actions

### 10.9 Quality Assurance

**Manual Review Workflow:**
- Flag uncertain verifications for manual review
- Allow operators to override AI decision
- Require supervisor approval for overrides

**Confidence Scoring:**
- Show AI confidence level for each verification
- Require manual review if confidence < 80%
- Track accuracy over time

**Video Quality Check:**
- Analyze video quality before processing
- Reject poor quality videos
- Provide feedback on video requirements

### 10.10 Compliance and Audit

**Regulatory Compliance:**
- GDPR compliance for data privacy
- Audit logs for all operations
- Data anonymization for reports

**Fraud Investigation Tools:**
- Detailed fraud case viewer
- Compare multiple bills from same trader
- Pattern detection across bills

**Reporting to Authorities:**
- Generate official fraud reports
- Digital signatures for authenticity
- Tamper-proof audit trail

### 10.11 Scalability

**Microservices Architecture:**
- Separate services for API, AI, database
- Independent scaling of components
- Better fault isolation

**Load Balancing:**
- Distribute requests across multiple servers
- Handle thousands of concurrent users
- Auto-scaling based on load

**Cloud Deployment:**
- Deploy on AWS/Azure/GCP
- Use managed services (RDS, S3, Lambda)
- Global CDN for static assets

### 10.12 Testing and Quality

**Automated Testing:**
- Unit tests for all functions
- Integration tests for API endpoints
- End-to-end tests for user workflows

**Performance Testing:**
- Load testing with 1000+ concurrent users
- Stress testing video processing
- Benchmark AI pipeline performance

**Continuous Integration:**
- Automated build and test pipeline
- Code quality checks (linting, formatting)
- Automated deployment to staging

---

## Summary

This design document provides a comprehensive blueprint for the Rice Mill AI system. The architecture is simple yet effective for a hackathon prototype, with clear paths for future enhancement. Key design decisions prioritize:

1. **Simplicity**: Vanilla tech stack, straightforward architecture
2. **Performance**: Frame skipping, indexing, connection pooling
3. **Security**: API key protection, input validation, SQL injection prevention
4. **Scalability**: Database design supports growth, clear upgrade paths
5. **User Experience**: Intuitive UI, clear feedback, expandable fraud details

The system is designed to be demo-ready while maintaining production-quality code structure and security practices.
