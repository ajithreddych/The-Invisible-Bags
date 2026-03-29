# 🧠 The Invisible Bags  
### AI-Powered Crop Entry Verification System for Government Rice Mills

---

## 📌 Overview
**The Invisible Bags** is an AI-powered system designed to eliminate fraud in government paddy procurement by automatically detecting, tracking, and counting jute bags using CCTV video footage.

It transforms existing surveillance systems into **intelligent verification systems**, ensuring that payments are made only for physically verified stock.

---

## 🚨 Problem Statement

Every harvest season, government procurement centers face a critical issue:

- Thousands of identical paddy bags are stored in rice mills
- Physical verification is nearly impossible
- Bills are generated based on manual input
- Middlemen inflate bag counts (e.g., 1200 → 1450)
- CCTV cameras only record activity but do not verify quantities

### ❗ Impact:
- Crores of public funds are lost
- MSP schemes are exploited
- Honest farmers suffer
- Fraud repeats across districts

---

## 🎯 Motivation

We are solving a **21st-century fraud using 21st-century technology**.

### The Gap:
- CCTV = Passive monitoring  
- No verification before payment  

### The Opportunity:
Transform CCTV into **Active Financial Guardians**

### GenAI Insight:
Detection alone is not enough →  
We add **Generative AI** to:
- Validate discrepancies
- Generate audit reports
- Support legal enforcement

---

## 💡 Proposed Solution

### 🧠 Rice Mill AI Auditor

An intelligent system that:

- Detects bags using **YOLOv8**
- Tracks objects using **ByteTrack**
- Counts bags crossing a virtual line
- Compares AI count with manual bill
- Uses **GenAI** to generate fraud alerts
- Blocks incorrect payments in real time

👉 **"Verify First, Pay Later"**

---

## ⚙️ System Workflow

1. **Bill Registration**
   - Enter bill number, vehicle details, manual bag count

2. **Video Upload**
   - Upload CCTV footage of truck entry

3. **AI Bag Detection**
   - Detect bags using object detection

4. **Tracking & Counting**
   - Track each bag uniquely
   - Count bags crossing a virtual line

5. **Comparison**
   - AI Count vs Manual Count

6. **Decision Engine**
   - Match → ✅ VERIFIED  
   - Mismatch → ❌ FRAUD ALERT  

7. **Dashboard**
   - Pending Bills  
   - Verified Bills  
   - Fraud Alerts  
   - Full audit logs  

---

## 🏗️ System Architecture (Code Representation)

```text
+----------------------+
|   CCTV Video Input   |
+----------+-----------+
           |
           v
+----------------------+
| Frame Extraction     |
| (OpenCV)             |
+----------+-----------+
           |
           v
+----------------------+
| Object Detection     |
| (YOLOv8 Model)       |
+----------+-----------+
           |
           v
+----------------------+
| Object Tracking      |
| (ByteTrack)          |
+----------+-----------+
           |
           v
+----------------------+
| Bag Counting Logic   |
+----------+-----------+
           |
           v
+------------------------------+
| Comparison Engine            |
| (Manual Count vs AI Count)   |
+----------+-------------------+
           |
   +-------+--------+
   |                |
   v                v
+-----------+   +----------------+
| VERIFIED  |   | FRAUD ALERT ⚠️ |
+-----------+   +----------------+
           |
           v
+-------------------------------+
| Dashboard & Audit Logs        |
| (Reports + Evidence Storage)  |
+-------------------------------+
