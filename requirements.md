# Rice Mill AI – Government Procurement Bag Verification System

## Overview

Rice Mill AI is a fraud detection system designed for government paddy procurement centers and rice mills. The system uses AI-powered video analysis to verify manual bag counts reported in procurement bills, helping prevent fraud in the agricultural supply chain.

## Problem Statement

In government paddy procurement centers, farmers deliver paddy bags and receive payment based on manually counted bags and weights. Fraud occurs when middlemen manipulate bag counts on manual bills, leading to:
- Financial losses for the government
- Unfair payments to farmers
- Lack of accountability in the procurement process
- Difficulty in detecting and proving fraud

Currently, there is no automated verification mechanism to cross-check manual bag counts against actual deliveries.

## Goals

1. Automate bag count verification using AI video analysis
2. Detect and flag fraudulent bag count discrepancies
3. Provide a simple web interface for bill registration and verification
4. Generate fraud alerts for investigation
5. Maintain a complete audit trail of all transactions
6. Reduce manual verification time and human error

## Scope

### In Scope

- Bill registration with manual bag count and weight data
- AI-based bag counting from vehicle entry videos
- Automated comparison of manual vs AI bag counts
- Fraud detection and alert generation
- Web-based user interface for all operations
- Database storage of bills, verification results, and fraud alerts
- Basic reporting views (verified bills, fraud alerts, all records)

### Out of Scope

- Real-time video streaming and processing
- Multi-camera support
- Advanced fraud pattern analysis
- User authentication and role-based access control (for hackathon prototype)
- Mobile application
- Integration with existing government systems
- Payment processing
- Farmer/trader management system
- Historical data migration
- Advanced analytics and dashboards

## User Roles

For this hackathon prototype, we assume a single user role:

**Procurement Officer**: Can register bills, upload videos, run AI verification, and view all reports.

## Functional Requirements

### 1. Bill Registration

- FR1.1: System shall provide a form to register new procurement bills
- FR1.2: System shall capture bill number (unique identifier)
- FR1.3: System shall capture bill date
- FR1.4: System shall capture farmer ID
- FR1.5: System shall capture trader ID
- FR1.6: System shall capture mill ID
- FR1.7: System shall capture vehicle number
- FR1.8: System shall capture manual bag count (integer)
- FR1.9: System shall capture manual total weight (decimal)
- FR1.10: System shall capture net weight per bag (decimal)
- FR1.11: System shall automatically set bill status to PENDING upon registration
- FR1.12: System shall validate that all required fields are filled before submission
- FR1.13: System shall prevent duplicate bill numbers
- FR1.14: System shall store bill registration timestamp

### 2. AI Verification

- FR2.1: System shall display a list of all bills with PENDING status
- FR2.2: System shall allow user to select a bill for verification
- FR2.3: System shall accept video file upload (entry video of vehicle with bags)
- FR2.4: System shall process uploaded video using Roboflow workflow model for bag detection
- FR2.5: System shall count unique bags using OpenCV-based logic
- FR2.6: System shall compare AI bag count with manual bag count
- FR2.7: System shall mark bill as VERIFIED if counts match (difference = 0)
- FR2.8: System shall mark bill as FRAUD if counts do not match (difference ≠ 0)
- FR2.9: System shall generate fraud alert when fraud is detected
- FR2.10: System shall store reconciliation results including manual count, AI count, and difference
- FR2.11: System shall store verification timestamp
- FR2.12: System shall display verification results immediately after processing

### 3. Verified Bills View

- FR3.1: System shall display a list of all bills with VERIFIED status
- FR3.2: System shall show bill number for each verified bill
- FR3.3: System shall show vehicle number for each verified bill
- FR3.4: System shall show manual bag count for each verified bill
- FR3.5: System shall show AI bag count for each verified bill
- FR3.6: System shall show difference (should be 0) for each verified bill
- FR3.7: System shall show verification timestamp for each verified bill
- FR3.8: System shall support sorting and filtering of verified bills

### 4. Fraud Alerts View

- FR4.1: System shall display a list of all bills where fraud was detected
- FR4.2: System shall show severity level for each fraud alert
- FR4.3: System shall show fraud message/description for each alert
- FR4.4: System shall show manual bag count for each fraud case
- FR4.5: System shall show AI bag count for each fraud case
- FR4.6: System shall show difference (discrepancy) for each fraud case
- FR4.7: System shall show alert generation timestamp
- FR4.8: System shall make each fraud alert row clickable
- FR4.9: System shall expand clicked row to show full bill details below the selected row
- FR4.10: System shall display bill number, farmer ID, trader ID, mill ID, and vehicle number in expanded view

### 5. All Records View

- FR5.1: System shall display a combined view of all bills
- FR5.2: System shall show bill details (bill_no, date, farmer_id, trader_id, mill_id, vehicle_no)
- FR5.3: System shall show manual bag count and weight information
- FR5.4: System shall show AI verification results (if available)
- FR5.5: System shall show current status (PENDING, VERIFIED, FRAUD)
- FR5.6: System shall show reconciliation difference (if verified)
- FR5.7: System shall support filtering by status
- FR5.8: System shall support sorting by date, bill number, or status

### 6. Backend API

- FR6.1: System shall provide POST /api/bills endpoint to create new bills
- FR6.2: System shall provide GET /api/bills endpoint to retrieve all bills
- FR6.3: System shall provide POST /api/ai/verify endpoint to process video and verify bag count
- FR6.4: System shall provide GET /api/verified-bills endpoint to retrieve verified bills
- FR6.5: System shall provide GET /api/fraud-alerts endpoint to retrieve fraud alerts
- FR6.6: System shall provide GET /api/all-records endpoint to retrieve combined view
- FR6.7: All API endpoints shall return JSON responses
- FR6.8: All API endpoints shall include appropriate HTTP status codes

## Non-Functional Requirements

### Performance

- NFR1.1: Video processing shall complete within 60 seconds for videos up to 2 minutes long
- NFR1.2: API response time shall be under 2 seconds for data retrieval endpoints
- NFR1.3: System shall support at least 10 concurrent users
- NFR1.4: Database queries shall execute within 1 second

### Security

- NFR2.1: System shall validate all user inputs to prevent SQL injection
- NFR2.2: System shall validate file uploads to accept only video formats
- NFR2.3: System shall limit video file size to 100MB maximum
- NFR2.4: System shall sanitize all data before database insertion

### Usability

- NFR3.1: User interface shall be responsive and work on desktop browsers
- NFR3.2: Forms shall provide clear validation error messages
- NFR3.3: System shall provide visual feedback during video processing
- NFR3.4: Navigation between pages shall be intuitive and consistent
- NFR3.5: System shall display loading indicators for long-running operations

### Reliability

- NFR4.1: System shall handle video processing errors gracefully
- NFR4.2: System shall log all errors for debugging
- NFR4.3: Database transactions shall be atomic (all-or-nothing)
- NFR4.4: System shall maintain data integrity during concurrent operations

### Maintainability

- NFR5.1: Code shall follow Python PEP 8 style guidelines
- NFR5.2: Frontend code shall be organized in separate HTML, CSS, and JS files
- NFR5.3: Database schema shall be documented
- NFR5.4: API endpoints shall be documented

### Constraints

- NFR6.1: System shall use Python Flask for backend
- NFR6.2: System shall use MySQL for database
- NFR6.3: System shall use Roboflow workflow model for bag detection
- NFR6.4: System shall use OpenCV for video processing and unique bag counting
- NFR6.5: System shall use vanilla HTML, CSS, JavaScript for frontend (no frameworks)
- NFR6.6: System is a hackathon prototype (not production-ready)

## Data Requirements

### Bills Table

- bill_id (primary key, auto-increment)
- bill_no (unique, varchar)
- bill_date (date)
- farmer_id (varchar)
- trader_id (varchar)
- mill_id (varchar)
- vehicle_no (varchar)
- manual_bag_count (integer)
- manual_total_weight (decimal)
- net_weight_per_bag (decimal)
- status (enum: PENDING, VERIFIED, FRAUD)
- created_at (timestamp)
- updated_at (timestamp)

### Reconciliation Table

- reconciliation_id (primary key, auto-increment)
- bill_id (foreign key to bills)
- manual_bag_count (integer)
- ai_bag_count (integer)
- difference (integer, calculated)
- video_path (varchar, path to uploaded video)
- verification_status (enum: VERIFIED, FRAUD)
- verified_at (timestamp)

### Fraud Alerts Table

- alert_id (primary key, auto-increment)
- bill_id (foreign key to bills)
- severity (enum: LOW, MEDIUM, HIGH)
- message (text)
- manual_bag_count (integer)
- ai_bag_count (integer)
- difference (integer)
- created_at (timestamp)

## API Requirements Summary

### POST /api/bills
- **Purpose**: Create new bill
- **Input**: JSON with bill details
- **Output**: Created bill with ID and status
- **Status Codes**: 201 (created), 400 (validation error), 500 (server error)

### GET /api/bills
- **Purpose**: Retrieve all bills or filter by status
- **Input**: Optional query parameter ?status=PENDING
- **Output**: Array of bill objects
- **Status Codes**: 200 (success), 500 (server error)

### POST /api/ai/verify
- **Purpose**: Process video and verify bag count
- **Input**: Multipart form data with bill_id and video file
- **Output**: Verification result with counts and status
- **Status Codes**: 200 (success), 400 (validation error), 404 (bill not found), 500 (server error)

### GET /api/verified-bills
- **Purpose**: Retrieve all verified bills
- **Output**: Array of verified bill objects with reconciliation data
- **Status Codes**: 200 (success), 500 (server error)

### GET /api/fraud-alerts
- **Purpose**: Retrieve all fraud alerts
- **Output**: Array of fraud alert objects
- **Status Codes**: 200 (success), 500 (server error)

### GET /api/all-records
- **Purpose**: Retrieve combined view of all bills with verification status
- **Output**: Array of bill objects with reconciliation and status data
- **Status Codes**: 200 (success), 500 (server error)

## Acceptance Criteria

### AC1: Bill Registration
- Given a user is on the bill registration page
- When they fill all required fields and submit
- Then a new bill is created with status PENDING
- And the bill appears in the AI verification page list
- And the bill number is unique in the system

### AC2: AI Bag Count Verification - Match
- Given a bill with status PENDING exists
- When a user uploads entry video and runs AI verification
- And the AI bag count matches the manual bag count
- Then the bill status changes to VERIFIED
- And the reconciliation record shows difference = 0
- And the bill appears in the verified bills page

### AC3: AI Bag Count Verification - Mismatch
- Given a bill with status PENDING exists
- When a user uploads entry video and runs AI verification
- And the AI bag count does not match the manual bag count
- Then the bill status changes to FRAUD
- And a fraud alert is generated
- And the fraud alert appears in the fraud alerts page
- And the alert shows the correct difference value

### AC4: Fraud Alert Details Expansion
- Given fraud alerts exist in the system
- When a user clicks on a fraud alert row
- Then the row expands to show full bill details
- And the details include bill_no, farmer_id, trader_id, mill_id, vehicle_no
- And the details include manual_bag_count, ai_bag_count, and difference

### AC5: Verified Bills Display
- Given verified bills exist in the system
- When a user navigates to the verified bills page
- Then only bills with status VERIFIED are displayed
- And each row shows bill_no, vehicle_no, manual_bag_count, ai_bag_count, difference, and verified_at
- And the difference value is 0 for all rows

### AC6: All Records View
- Given bills with various statuses exist in the system
- When a user navigates to the all records page
- Then all bills are displayed regardless of status
- And each row shows bill details, verification results (if available), and current status
- And the user can filter by status (PENDING, VERIFIED, FRAUD)

### AC7: Video Processing
- Given a valid video file is uploaded
- When the AI verification process runs
- Then the Roboflow model detects bags in the video
- And the OpenCV logic counts unique bags
- And the AI bag count is stored in the reconciliation table
- And the processing completes within 60 seconds

### AC8: Data Integrity
- Given multiple bills are being processed
- When concurrent operations occur
- Then each bill maintains its own verification state
- And no data corruption occurs
- And all database constraints are enforced

### AC9: Error Handling
- Given invalid data is submitted
- When the API receives the request
- Then appropriate validation errors are returned
- And the user sees clear error messages
- And no partial data is saved to the database

### AC10: API Responses
- Given any API endpoint is called
- When the request is processed
- Then the response is in valid JSON format
- And the appropriate HTTP status code is returned
- And error responses include descriptive messages
