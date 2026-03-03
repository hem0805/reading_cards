let currentImage = null;
let stream = null;

/* ===========================
   SIMPLE MODE SWITCH
=========================== */

document.getElementById("uploadBtn").addEventListener("click", () => {

    // Toggle active state
    document.getElementById("uploadBtn").classList.add("active");
    document.getElementById("cameraBtn").classList.remove("active");

    document.getElementById("uploadSection").style.display = "block";
    document.getElementById("cameraSection").style.display = "none";

    stopCamera();
});

document.getElementById("cameraBtn").addEventListener("click", () => {

    // Toggle active state
    document.getElementById("cameraBtn").classList.add("active");
    document.getElementById("uploadBtn").classList.remove("active");

    document.getElementById("uploadSection").style.display = "none";
    document.getElementById("cameraSection").style.display = "block";

    startCamera();
});

/* ===========================
   CAMERA
=========================== */

function startCamera() {

    if (stream) return;

    const video = document.getElementById("video");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera not supported in this browser.");
        return;
    }

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(s => {
            stream = s;
            video.srcObject = stream;
        })
        .catch(err => {
            console.error(err);
            alert("Camera permission denied.");
        });
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    const video = document.getElementById("video");
    if (video) video.srcObject = null;
}

function captureImage() {

    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");

    if (!video.srcObject) {
        alert("Camera not started.");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL("image/png");

    processImage(imageData);
}

/* ===========================
   UPLOAD
=========================== */

function handleUpload(event) {

    if (!event.target.files.length) return;

    const file = event.target.files[0];

    document.getElementById("fileName").innerText = file.name;

    const reader = new FileReader();

    reader.onload = function (e) {
        processImage(e.target.result);
    };

    reader.readAsDataURL(file);
}

/* ===========================
   PROCESS IMAGE
=========================== */

function processImage(imageData) {

    currentImage = imageData;

    // Show original image
    document.getElementById("originalImage").src = imageData;

    const overlay = document.getElementById("scannerOverlay");
    if (overlay) overlay.style.display = "flex";

    fetch("/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: imageData })
    })
    .then(res => res.json())
    .then(data => {

        if (overlay) overlay.style.display = "none";

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById("resultSection").style.display = "block";
        document.getElementById("clearBtn").style.display = "inline-block";

        document.getElementById("annotatedImage").src = data.annotated;

        document.getElementById("name").value = data.fields.Name || "";
        document.getElementById("designation").value = data.fields.Designation || "";
        document.getElementById("phone").value = data.fields.Phone || "";
        document.getElementById("email").value = data.fields.Email || "";
        document.getElementById("website").value = data.fields.Website || "";
        document.getElementById("address").value = data.fields.Address || "";

        updatePreview(data.fields);
    })
    .catch(err => {
        if (overlay) overlay.style.display = "none";
        console.error(err);
        alert("Extraction failed.");
    });
}

/* ===========================
   PREVIEW TABLE
=========================== */

function updatePreview(fields) {

    const table = document.getElementById("previewTable");

    table.innerHTML = `
        <tr>
            <th>Name</th>
            <th>Designation</th>
            <th>Phone</th>
            <th>Email</th>
            <th>Website</th>
            <th>Address</th>
        </tr>
        <tr>
            <td>${fields.Name || ""}</td>
            <td>${fields.Designation || ""}</td>
            <td>${fields.Phone || ""}</td>
            <td>${fields.Email || ""}</td>
            <td>${fields.Website || ""}</td>
            <td>${fields.Address || ""}</td>
        </tr>
    `;
}

/* ===========================
   SAVE
=========================== */

function saveRecord() {

    const record = {
        Name: document.getElementById("name").value.trim(),
        Designation: document.getElementById("designation").value.trim(),
        Phone: document.getElementById("phone").value.trim(),
        Email: document.getElementById("email").value.trim().toLowerCase(),
        Website: document.getElementById("website").value.trim(),
        Address: document.getElementById("address").value.trim()
    };

    fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record)
    })
    .then(res => res.json())
    .then(data => {

        if (data.success) {

            document.getElementById("vcardContainer").innerHTML =
                `<a class="vcard-link" href="${data.vcard}" download>
                    📱 Download Contact (.vcf)
                 </a>`;

            alert("Record saved successfully!");

        } else if (data.duplicate === "email") {

            alert("⚠ A contact with this email already exists.");

        } else if (data.duplicate === "phone") {

            alert("⚠ A contact with this phone already exists.");

        } else {

            alert("Save failed.");
        }
    })
    .catch(err => {
        console.error("Save error:", err);
        alert("Save failed.");
    });
}

/* ===========================
   CLEAR
=========================== */

function resetAll() {

    stopCamera();

    document.getElementById("resultSection").style.display = "none";
    document.getElementById("clearBtn").style.display = "none";

    document.getElementById("originalImage").src = "";
    document.getElementById("annotatedImage").src = "";

    document.getElementById("fileName").innerText = "";
    document.getElementById("fileInput").value = "";

    ["name","designation","phone","email","website","address"].forEach(id => {
        document.getElementById(id).value = "";
    });

    document.getElementById("previewTable").innerHTML = "";
    document.getElementById("vcardContainer").innerHTML = "";

    const overlay = document.getElementById("scannerOverlay");
    if (overlay) overlay.style.display = "none";

    currentImage = null;
}