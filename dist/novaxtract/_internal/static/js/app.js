// ===============================
// MODE SWITCH
// ===============================

function setMode(mode) {

    const uploadSection = document.getElementById("uploadSection");
    const cameraSection = document.getElementById("cameraSection");

    const uploadBtn = document.getElementById("uploadBtn");
    const cameraBtn = document.getElementById("cameraBtn");

    uploadBtn.classList.remove("active");
    cameraBtn.classList.remove("active");

    if (mode === "upload") {

        uploadSection.style.display = "flex";
        cameraSection.style.display = "none";

        uploadBtn.classList.add("active");

        stopCamera();

    } else {

        uploadSection.style.display = "none";
        cameraSection.style.display = "flex";

        cameraBtn.classList.add("active");

        startCamera();
    }
}


// ===============================
// CAMERA
// ===============================

let stream = null;

function startCamera() {

    const video = document.getElementById("video");

    navigator.mediaDevices.getUserMedia({video:true})
    .then(function(s){

        stream = s;
        video.srcObject = stream;

    })
    .catch(function(){

        alert("Camera access denied");

    });
}

function stopCamera(){

    if(!stream) return;

    stream.getTracks().forEach(track => track.stop());
    stream = null;
}


// ===============================
// CAPTURE IMAGE
// ===============================

function captureImage(){

    const video = document.getElementById("video");

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(video,0,0);

    canvas.toBlob(function(blob){

        sendImage(blob);

    },"image/jpeg");
}


// ===============================
// UPLOAD IMAGE
// ===============================

function handleUpload(event){

    const file = event.target.files[0];

    if(!file){
        alert("No file selected");
        return;
    }

    sendImage(file);
}


// ===============================
// SEND IMAGE
// ===============================

function sendImage(file){

    const loader = document.getElementById("loader");
    loader.style.display = "flex";

    const formData = new FormData();
    formData.append("file",file);

    fetch("/extract",{
        method:"POST",
        body:formData
    })
    .then(res=>res.json())
    .then(data=>{

        loader.style.display = "none";

        if(data.error){
            alert(data.error);
            return;
        }

        // document.getElementById("originalImage").src = URL.createObjectURL(file);
        const url = URL.createObjectURL(file);
        document.getElementById("originalImage").src = url;
        setTimeout(()=>URL.revokeObjectURL(url),5000);

        document.getElementById("annotatedImage").src =data.annotated_image + "?t=" + new Date().getTime();

        fillFields(data.fields);

        document.getElementById("dashboard").style.display="grid";
        document.getElementById("records").style.display="block";

    })
    .catch(()=>{

        loader.style.display = "none";
        alert("Extraction failed");

    });
}


// ===============================
// FILL FIELDS
// ===============================

function fillFields(fields){

    document.getElementById("name").value = fields.Name || "";
    document.getElementById("designation").value = fields.Designation || "";
    document.getElementById("phone").value = fields.Phone || "";
    document.getElementById("email").value = fields.Email || "";
    document.getElementById("website").value = fields.Website || "";
    document.getElementById("address").value = fields.Address || "";
}


// ===============================
// SAVE RECORD
// ===============================

function saveRecord(){

    const data = {

        name:document.getElementById("name").value,
        designation:document.getElementById("designation").value,
        phone:document.getElementById("phone").value,
        email:document.getElementById("email").value,
        website:document.getElementById("website").value,
        address:document.getElementById("address").value
    };

    fetch("/save",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    })
    .then(res=>res.json())
    .then(()=>{

        appendRow(data);

    });
}


// ===============================
// APPEND ROW
// ===============================

function appendRow(data){

    const table = document.getElementById("previewTable").querySelector("tbody");

    const row = document.createElement("tr");

    row.innerHTML = `
        <td>${data.name}</td>
        <td>${data.designation}</td>
        <td>${data.phone}</td>
        <td>${data.email}</td>
        <td>${data.website}</td>
        <td>${data.address}</td>
    `;

    table.appendChild(row);
}


// ===============================
// CLEAR FIELDS
// ===============================

function clearFields(){

    document.getElementById("name").value="";
    document.getElementById("designation").value="";
    document.getElementById("phone").value="";
    document.getElementById("email").value="";
    document.getElementById("website").value="";
    document.getElementById("address").value="";
}


// ===============================
// CLEAR EXTRACTION
// ===============================

function clearExtraction(){

    clearFields();

    document.getElementById("originalImage").src="";
    document.getElementById("annotatedImage").src="";

    document.getElementById("dashboard").style.display="none";

    const uploadBtn = document.getElementById("uploadBtn");
    const cameraBtn = document.getElementById("cameraBtn");

    // reset file input
    const fileInput = document.getElementById("fileInput");
    if(fileInput) fileInput.value="";

    if(uploadBtn.classList.contains("active")){
        document.getElementById("uploadSection").style.display="flex";
        document.getElementById("cameraSection").style.display="none";
    }
    else{
        document.getElementById("uploadSection").style.display="none";
        document.getElementById("cameraSection").style.display="flex";
    }
}

// ===============================
// EXPORT CSV
// ===============================

function exportCSV(){

    window.location.href="/export_csv";

}

// ===============================
// SPACEBAR CAPTURE SUPPORT
// ===============================

document.addEventListener("keydown", function(event) {

    // check if spacebar pressed
    if (event.code === "Space") {

        const cameraSection = document.getElementById("cameraSection");

        // only capture if camera section is visible
        if (cameraSection && cameraSection.style.display !== "none") {

            event.preventDefault(); // stop page scrolling
            captureImage();

        }
    }

});