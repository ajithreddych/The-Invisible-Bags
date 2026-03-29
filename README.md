# 🧠 The Invisible Bags  
### AI-Powered Crop Entry Verification System for Government Rice Mills

---

## 📌 Overview
**The Invisible Bags** is an AI-driven system designed to prevent fraud in government paddy procurement by automatically detecting and counting jute bags using CCTV footage.

It transforms traditional surveillance systems into **active financial verification tools**, ensuring that payments are made only for physically verified stock.

---

## 🚨 Problem Statement
Every harvest season, government procurement centers face a major issue:

- Paddy bags are stored in large quantities
- Manual counting is unreliable and error-prone
- Bills are generated based on human input
- Middlemen inflate numbers (e.g., 1200 → 1450 bags)
- CCTV cameras only record — they don’t verify

👉 This leads to:
- Financial loss to government (MSP funds misuse)
- Fraudulent claims (ghost stock)
- No accountability or real-time validation

📎 Source: Hackathon Presentation :contentReference[oaicite:0]{index=0}  

---

## 💡 Proposed Solution
We propose **Rice Mill AI Auditor**, an intelligent system that:

- Uses **Computer Vision (YOLOv8 + ByteTrack)** to detect and track bags
- Counts bags in real-time as they enter the warehouse
- Compares AI count with manual bill entries
- Uses **Generative AI** to validate and generate fraud reports
- Triggers **real-time fraud alerts**

👉 Ensures: **"Verify First, Pay Later"**

📎 Source: Project Description :contentReference[oaicite:1]{index=1}  

---

## ⚙️ System Workflow

1. **Bill Registration**
   - Enter manual bill details (vehicle number, bag count, etc.)

2. **Video Upload**
   - Upload CCTV footage of vehicle entry

3. **AI Bag Detection**
   - Detects and tracks each bag crossing a virtual line

4. **Counting & Comparison**
   - AI Count vs Manual Count

5. **Decision**
   - ✅ Match → VERIFIED  
   - ❌ Mismatch → FRAUD ALERT  

6. **Dashboard Reporting**
   - Pending Bills  
   - Verified Bills  
   - Fraud Alerts  
   - Complete Audit Logs  

---

## 🎯 Key Features

- 📹 Real-time video-based bag detection
- 🎯 Accurate counting using object tracking
- ⚡ Fraud detection & instant alerts
- 🧾 Automated audit reports (GenAI)
- 🛡️ Pre-payment verification system
- 📊 Dashboard for monitoring all transactions

---

## 🧠 Tech Stack

### 🔹 AI/ML
- YOLOv8 (Object Detection)
- ByteTrack (Object Tracking)
- OpenCV

### 🔹 Generative AI
- Fraud report generation
- Legal notice drafting

### 🔹 Backend
- Python

### 🔹 Frontend
- HTML, CSS, JavaScript

### 🔹 Tools
- Roboflow (dataset & training)
- Supervision (video processing)
- GitHub

---

## 🏗️ Architecture
