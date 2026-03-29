// Prevent accidental form refresh globally
window.addEventListener("beforeunload", function (e) {
  e.preventDefault();
  e.returnValue = "";
});
document.addEventListener("DOMContentLoaded", function () {
const BACKEND_URL = "http://127.0.0.1:5000";

// --------------------
// GLOBAL UI ELEMENTS
// --------------------
const backendStatus = document.getElementById("backendStatus");
const dot = document.querySelector(".dot");

const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");

const pageTitle = document.getElementById("pageTitle");
const pageSub = document.getElementById("pageSub");

const sidebar = document.querySelector(".sidebar");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");

// --------------------
// PAGE META
// --------------------
const pageMeta = {
  registration: {
    title: "Bill Registration",
    sub: "Register procurement bill details for AI verification."
  },
  aiVerification: {
    title: "AI Verification",
    sub: "Select pending bill and upload entry video to count bags."
  },
  verifiedBills: {
    title: "Verified Bills",
    sub: "Bills where manual count matches AI counted bags."
  },
  fraudAlerts: {
    title: "Fraud Alerts",
    sub: "Bills flagged due to mismatch or suspicious activity."
  },
  allDetails: {
    title: "All Records",
    sub: "Complete view of bills, AI batches, reconciliation and alerts."
  }
};

// --------------------
// BACKEND CHECK
// --------------------
async function checkBackend() {
  try {
    const res = await fetch(`${BACKEND_URL}/`);
    if (!res.ok) throw new Error("Backend not reachable");

    backendStatus.textContent = "Online";
    dot.style.background = "#22c55e";
  } catch (err) {
    backendStatus.textContent = "Offline";
    dot.style.background = "#ff6b6b";
  }
}

// --------------------
// SIDEBAR NAV
// --------------------
function switchPage(pageId) {
  pages.forEach(p => p.classList.remove("active"));
  document.getElementById(pageId).classList.add("active");

  navItems.forEach(n => n.classList.remove("active"));
  document.querySelector(`[data-page="${pageId}"]`).classList.add("active");

  pageTitle.textContent = pageMeta[pageId].title;
  pageSub.textContent = pageMeta[pageId].sub;

  sidebar.classList.remove("open");

  // auto load per page
  if (pageId === "aiVerification") refreshPendingBillsListOnly();
  if (pageId === "verifiedBills") loadVerifiedBills();
  if (pageId === "fraudAlerts") loadFraudAlerts();
  if (pageId === "allDetails") loadAllRecords();
}


navItems.forEach(btn => {
  btn.addEventListener("click", () => {
    switchPage(btn.dataset.page);
  });
});

mobileMenuBtn.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

// --------------------
// BILL REGISTRATION
// --------------------
const billForm = document.getElementById("billForm");
const messageBox = document.getElementById("messageBox");

function showMessage(type, text) {
  messageBox.classList.remove("hidden", "success", "error");
  messageBox.classList.add(type);
  messageBox.textContent = text;
}

billForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(billForm);

  const payload = {
    bill_no: formData.get("bill_no"),
    bill_date: formData.get("bill_date"),
    farmer_id: formData.get("farmer_id"),
    trader_id: formData.get("trader_id"),
    mill_id: formData.get("mill_id"),
    vehicle_no: formData.get("vehicle_no"),
    manual_bag_count: Number(formData.get("manual_bag_count")),
    manual_total_weight: Number(formData.get("manual_total_weight")),
    net_weight_per_bag: Number(formData.get("net_weight_per_bag")),
  };

  if (
    !payload.bill_no ||
    !payload.bill_date ||
    !payload.farmer_id ||
    !payload.trader_id ||
    !payload.mill_id ||
    !payload.vehicle_no ||
    payload.manual_bag_count <= 0 ||
    payload.manual_total_weight <= 0 ||
    payload.net_weight_per_bag <= 0
  ) {
    showMessage("error", "❌ Please fill all required fields correctly.");
    return;
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/bills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      showMessage("error", data.message || "❌ Failed to register bill");
      return;
    }

    showMessage("success", "✅ Bill Registered Successfully! Status = PENDING");
    billForm.reset();
    refreshPendingBillsListOnly();
    
  } catch (err) {
    showMessage("error", "❌ Backend not reachable. Start Flask server.");
  }
});

// --------------------
// AI VERIFICATION UI
// --------------------
const pendingBillsList = document.getElementById("pendingBillsList");
const billSearch = document.getElementById("billSearch");
const refreshBillsBtn = document.getElementById("refreshBillsBtn");

const selectedBillBox = document.getElementById("selectedBillBox");
const videoInput = document.getElementById("videoInput");
const runAiBtn = document.getElementById("runAiBtn");

const aiMessage = document.getElementById("aiMessage");
const aiResultBox = document.getElementById("aiResultBox");

const aiBagCount = document.getElementById("aiBagCount");
const aiTotalWeight = document.getElementById("aiTotalWeight");
const manualBagCount = document.getElementById("manualBagCount");
const manualTotalWeight = document.getElementById("manualTotalWeight");
const diffCount = document.getElementById("diffCount");

let allPendingBills = [];
let selectedBill = null;

function showAiMessage(type, text) {
  aiMessage.classList.remove("hidden", "success", "error");
  aiMessage.classList.add(type);
  aiMessage.textContent = text;
}

function hideAiMessage() {
  aiMessage.classList.add("hidden");
}

function clearAiResult() {
  aiResultBox.classList.add("hidden");
  aiBagCount.textContent = "-";
  aiTotalWeight.textContent = "-";
  manualBagCount.textContent = "-";
  manualTotalWeight.textContent = "-";
  diffCount.textContent = "-";
}

function renderBills(bills) {
  pendingBillsList.innerHTML = "";

  if (!bills.length) {
    pendingBillsList.innerHTML = `
      <div class="empty-box">
        No pending bills found.
      </div>
    `;
    return;
  }

  bills.forEach((bill) => {
    const div = document.createElement("div");
    div.className = "bill-item";

    div.innerHTML = `
      <div class="bill-top">
        <div class="bill-no">${bill.bill_no}</div>
        <div class="badge">${bill.status}</div>
      </div>

      <div class="bill-meta">
        <div><b>Vehicle:</b> ${bill.vehicle_no}</div>
        <div><b>Manual Bags:</b> ${bill.manual_bag_count}</div>
        <div><b>Net/bag:</b> ${bill.net_weight_per_bag} kg</div>
      </div>
    `;

    div.addEventListener("click", () => {
      document.querySelectorAll(".bill-item").forEach((x) => x.classList.remove("active"));
      div.classList.add("active");
      selectBill(bill);
    });

    pendingBillsList.appendChild(div);
  });
}

function selectBill(bill) {
  selectedBill = bill;
  runAiBtn.disabled = false;
  videoInput.value = "";
  hideAiMessage();
  clearAiResult();

  selectedBillBox.innerHTML = `
    <div class="selected-grid">
      <div class="kv"><span class="k">Bill No</span><span class="v">${bill.bill_no}</span></div>
      <div class="kv"><span class="k">Bill Date</span><span class="v">${bill.bill_date || "-"}</span></div>
      <div class="kv"><span class="k">Farmer ID</span><span class="v">${bill.farmer_id}</span></div>
      <div class="kv"><span class="k">Trader ID</span><span class="v">${bill.trader_id}</span></div>
      <div class="kv"><span class="k">Vehicle No</span><span class="v">${bill.vehicle_no}</span></div>
      <div class="kv"><span class="k">Manual Bag Count</span><span class="v">${bill.manual_bag_count}</span></div>
      <div class="kv"><span class="k">Total Weight</span><span class="v">${bill.manual_total_weight} kg</span></div>
      <div class="kv"><span class="k">Net Weight / Bag</span><span class="v">${bill.net_weight_per_bag} kg</span></div>
    </div>
  `;
}

async function refreshPendingBillsListOnly() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/bills`);
    const data = await res.json();

    if (!res.ok) return;

    allPendingBills = (data.bills || []).filter(b => b.status === "PENDING");

    // keep current search filter
    const q = billSearch.value.trim().toLowerCase();
    const filtered = q
      ? allPendingBills.filter((b) => b.bill_no.toLowerCase().includes(q))
      : allPendingBills;

    renderBills(filtered);

  } catch (err) {
    // do nothing (avoid breaking UI)
  }
}

billSearch.addEventListener("input", () => {
  const q = billSearch.value.trim().toLowerCase();
  const filtered = allPendingBills.filter((b) =>
    b.bill_no.toLowerCase().includes(q)
  );
  renderBills(filtered);
});

refreshBillsBtn.addEventListener("click", () => {
  billSearch.value = "";
setTimeout(() => {
  refreshPendingBillsListOnly();
}, 1000);


});

videoInput.addEventListener("change", () => {
  if (!selectedBill) {
    runAiBtn.disabled = true;
    return;
  }
  runAiBtn.disabled = videoInput.files.length === 0;
});


runAiBtn.addEventListener("click", async (e) => {

  e.preventDefault();   // ✅ keep this

  if (!selectedBill) {
    showAiMessage("error", "❌ Please select a bill first.");
    return;
  }

  if (!videoInput.files.length) {
    showAiMessage("error", "❌ Please upload a video file.");
    return;
  }

  const videoFile = videoInput.files[0];

  const formData = new FormData();
  formData.append("bill_id", selectedBill.id);
  formData.append("video", videoFile);

  runAiBtn.disabled = true;
  runAiBtn.textContent = "⏳ Processing...";
  showAiMessage("success", "Uploading & processing video... Please wait.");
  clearAiResult();

  try {
    const res = await fetch(`${BACKEND_URL}/api/ai/verify`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      showAiMessage("error", data.message || "❌ AI verification failed");
      return;
    }

    aiBagCount.textContent = data.ai_bag_count;
    aiTotalWeight.textContent = Number(data.ai_total_weight).toFixed(2);
    manualBagCount.textContent = data.manual_bag_count;
    manualTotalWeight.textContent = Number(data.manual_total_weight).toFixed(2);
    diffCount.textContent = data.difference;

    aiResultBox.classList.remove("hidden");

    if (data.result === "MATCH") {
      showAiMessage("success", "✅ VERIFIED: Manual count matches AI count.");
    } else {
      showAiMessage("error", "🚨 MISMATCH: Fraud alert generated.");
    }

  } catch (err) {
    showAiMessage("error", "❌ Backend not reachable.");
  } finally {
    runAiBtn.disabled = false;
    runAiBtn.textContent = "Run AI Bag Counting";
  }

});



// --------------------
// VERIFIED BILLS PAGE
// --------------------
const verifiedBody = document.getElementById("verifiedBody");
const verifiedSearch = document.getElementById("verifiedSearch");
const refreshVerifiedBtn = document.getElementById("refreshVerifiedBtn");

let verifiedBills = [];

function renderVerifiedBills(rows) {
  verifiedBody.innerHTML = "";

  if (!rows.length) {
    verifiedBody.innerHTML = `<tr><td colspan="7" class="muted-td">No verified bills found.</td></tr>`;
    return;
  }

  rows.forEach((b) => {
    verifiedBody.innerHTML += `
      <tr>
        <td><b>${b.bill_no}</b></td>
        <td>${b.vehicle_no || "-"}</td>
        <td>${b.manual_bag_count}</td>
        <td>${b.ai_bag_count}</td>
        <td>${b.difference}</td>
        <td><span class="pill success">VERIFIED</span></td>
        <td>${b.verified_at || "-"}</td>
      </tr>
    `;
  });
}

async function loadVerifiedBills() {
  verifiedBody.innerHTML = `<tr><td colspan="7" class="muted-td">Loading...</td></tr>`;

  try {
    const res = await fetch(`${BACKEND_URL}/api/verified-bills`);
    const data = await res.json();

    if (!res.ok) {
      verifiedBody.innerHTML = `<tr><td colspan="7" class="muted-td">Failed to load.</td></tr>`;
      return;
    }

    verifiedBills = data.bills || [];
    applyVerifiedSearch();
  } catch (err) {
    verifiedBody.innerHTML = `<tr><td colspan="7" class="muted-td">Backend not reachable.</td></tr>`;
  }
}

function applyVerifiedSearch() {
  const q = verifiedSearch.value.trim().toLowerCase();
  const filtered = q
    ? verifiedBills.filter(b => (b.bill_no || "").toLowerCase().includes(q))
    : verifiedBills;

  renderVerifiedBills(filtered);
}

verifiedSearch.addEventListener("input", applyVerifiedSearch);
refreshVerifiedBtn.addEventListener("click", loadVerifiedBills);


// --------------------
// FRAUD ALERTS PAGE
// --------------------
const fraudBody = document.getElementById("fraudBody");
const fraudSearch = document.getElementById("fraudSearch");
const refreshFraudBtn = document.getElementById("refreshFraudBtn");

let fraudAlerts = [];

// FRAUD DETAILS UI
const fraudDetailsBox = document.getElementById("fraudDetailsBox");

const fdBill = document.getElementById("fdBill");
const fdVehicle = document.getElementById("fdVehicle");
const fdManual = document.getElementById("fdManual");
const fdAi = document.getElementById("fdAi");
const fdDiff = document.getElementById("fdDiff");
const fdSeverity = document.getElementById("fdSeverity");
const fdMessage = document.getElementById("fdMessage");
const fdTime = document.getElementById("fdTime");

function showFraudDetails(f) {
  fraudDetailsBox.classList.remove("hidden");

  fdBill.textContent = f.bill_no || "-";
  fdVehicle.textContent = f.vehicle_no || "-";
  fdManual.textContent = f.manual_bag_count ?? "-";
  fdAi.textContent = f.ai_bag_count ?? "-";
  fdDiff.textContent = f.difference ?? "-";
  fdSeverity.textContent = f.severity || "HIGH";
  fdMessage.textContent = f.message || "Bag count mismatch detected.";
  fdTime.textContent = f.alert_time || "-";
}

function renderFraudAlerts(rows) {
  fraudBody.innerHTML = "";

  if (!rows.length) {
    fraudBody.innerHTML = `
      <tr>
        <td colspan="7" class="muted-td">No fraud alerts found.</td>
      </tr>
    `;
    return;
  }

  rows.forEach((f, i) => {

    // MAIN ROW
    const tr = document.createElement("tr");
    tr.classList.add("fraud-row");
    tr.setAttribute("data-index", i);

    tr.innerHTML = `
      <td><b>${f.bill_no}</b></td>
      <td>${f.vehicle_no || "-"}</td>
      <td>${f.manual_bag_count ?? "-"}</td>
      <td>${f.ai_bag_count ?? "-"}</td>
      <td>${f.difference ?? "-"}</td>
      <td><span class="pill danger">${f.severity || "MISMATCH"}</span></td>
      <td>${f.alert_time || "-"}</td>
    `;

    // EXPAND ROW (hidden by default)
    const expandTr = document.createElement("tr");
    expandTr.classList.add("expand-row");
    expandTr.style.display = "none"; // hidden

    expandTr.innerHTML = `
      <td colspan="7">
        <div class="expand-box">
          <div class="expand-title">Fraud Details</div>

          <div class="expand-grid">
            <div class="expand-item">
              <span class="k">Bill No</span>
              <span class="v">${f.bill_no}</span>
            </div>

            <div class="expand-item">
              <span class="k">Vehicle</span>
              <span class="v">${f.vehicle_no || "-"}</span>
            </div>

            <div class="expand-item">
              <span class="k">Manual Bags</span>
              <span class="v">${f.manual_bag_count ?? "-"}</span>
            </div>

            <div class="expand-item">
              <span class="k">AI Bags</span>
              <span class="v">${f.ai_bag_count ?? "-"}</span>
            </div>

            <div class="expand-item">
              <span class="k">Difference</span>
              <span class="v">${f.difference ?? "-"}</span>
            </div>

            <div class="expand-item">
              <span class="k">Severity</span>
              <span class="v">${f.severity || "HIGH"}</span>
            </div>

            <div class="expand-item full">
              <span class="k">Fraud Reason / Message</span>
              <span class="v big">${f.message || "Bag count mismatch detected."}</span>
            </div>

            <div class="expand-item full">
              <span class="k">Alert Time</span>
              <span class="v">${f.alert_time || "-"}</span>
            </div>
          </div>
        </div>
      </td>
    `;


    fraudBody.appendChild(tr);
    fraudBody.appendChild(expandTr);
  });
}

/* ✅ CLICK HANDLER FOR EXPANDER */
fraudBody.onclick = function (e) {
  const tr = e.target.closest("tr");
  if (!tr) return;

  // if clicked on expand row itself, ignore
  if (tr.classList.contains("expand-row")) return;

  const index = tr.getAttribute("data-index");
  if (index === null) return;

  const expandRow = tr.nextElementSibling;

  // close all other expanded rows
  document.querySelectorAll("#fraudBody .expand-row").forEach(r => {
    r.style.display = "none";
  });

  document.querySelectorAll("#fraudBody .fraud-row").forEach(r => {
    r.classList.remove("active-row");
  });

  // toggle expand
  tr.classList.add("active-row");

  if (expandRow && expandRow.classList.contains("expand-row")) {
    expandRow.style.display = "table-row";
  }
};


async function loadFraudAlerts() {
  fraudBody.innerHTML = `<tr><td colspan="7" class="muted-td">Loading...</td></tr>`;

  try {
    const res = await fetch(`${BACKEND_URL}/api/fraud-alerts`);
    const data = await res.json();

    if (!res.ok) {
      fraudBody.innerHTML = `<tr><td colspan="7" class="muted-td">Failed to load.</td></tr>`;
      return;
    }

    fraudAlerts = data.alerts || [];
    applyFraudSearch();
  } catch (err) {
    fraudBody.innerHTML = `<tr><td colspan="7" class="muted-td">Backend not reachable.</td></tr>`;
  }
}

function applyFraudSearch() {
  const q = fraudSearch.value.trim().toLowerCase();

  const filtered = q
    ? fraudAlerts.filter(f => (f.bill_no || "").toLowerCase().includes(q))
    : fraudAlerts;

  renderFraudAlerts(filtered);

  fraudDetailsBox.classList.add("hidden");
}

fraudSearch.addEventListener("input", applyFraudSearch);
refreshFraudBtn.addEventListener("click", loadFraudAlerts);



// --------------------
// ALL RECORDS PAGE
// --------------------
const allBody = document.getElementById("allBody");
const allSearch = document.getElementById("allSearch");
const refreshAllBtn = document.getElementById("refreshAllBtn");

let allRecords = [];

function renderAllRecords(rows) {
  allBody.innerHTML = "";

  if (!rows.length) {
    allBody.innerHTML = `<tr><td colspan="9" class="muted-td">No records found.</td></tr>`;
    return;
  }

  rows.forEach((r) => {
    const statusPill =
      r.status === "VERIFIED"
        ? `<span class="pill success">VERIFIED</span>`
        : r.status === "FRAUD"
        ? `<span class="pill danger">FRAUD</span>`
        : `<span class="pill pending">PENDING</span>`;

    allBody.innerHTML += `
      <tr>
        <td><b>${r.bill_no}</b></td>
        <td>${r.farmer_id || "-"}</td>
        <td>${r.trader_id || "-"}</td>
        <td>${r.vehicle_no || "-"}</td>
        <td>${r.manual_bag_count || "-"}</td>
        <td>${r.ai_bag_count ?? "-"}</td>
        <td>${r.difference ?? "-"}</td>
        <td>${statusPill}</td>
        <td>${r.updated_at || "-"}</td>
      </tr>
    `;
  });
}

async function loadAllRecords() {
  allBody.innerHTML = `<tr><td colspan="9" class="muted-td">Loading...</td></tr>`;

  try {
    const res = await fetch(`${BACKEND_URL}/api/all-records`);
    const data = await res.json();

    if (!res.ok) {
      allBody.innerHTML = `<tr><td colspan="9" class="muted-td">Failed to load.</td></tr>`;
      return;
    }

    allRecords = data.records || [];
    applyAllSearch();
  } catch (err) {
    allBody.innerHTML = `<tr><td colspan="9" class="muted-td">Backend not reachable.</td></tr>`;
  }
}

function applyAllSearch() {
  const q = allSearch.value.trim().toLowerCase();

  const filtered = q
    ? allRecords.filter((r) => {
        return (
          (r.bill_no || "").toLowerCase().includes(q) ||
          (r.farmer_id || "").toLowerCase().includes(q) ||
          (r.trader_id || "").toLowerCase().includes(q) ||
          (r.vehicle_no || "").toLowerCase().includes(q)
        );
      })
    : allRecords;

  renderAllRecords(filtered);
}

allSearch.addEventListener("input", applyAllSearch);
refreshAllBtn.addEventListener("click", loadAllRecords);



// init
checkBackend();
document.addEventListener("DOMContentLoaded", () => {
  switchPage("registration");
});

});
