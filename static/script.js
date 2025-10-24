let resumeText = "";

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js";

document.addEventListener("DOMContentLoaded", function() {
    // Tab Switch
    document.getElementById("pdfTab").addEventListener("click", () =>
        switchTab("pdf")
    );
    document.getElementById("textTab").addEventListener("click", () =>
        switchTab("text")
    );

    // Job Description toggle
    const jobDescCheck = document.getElementById("jobDescCheck");
    if (jobDescCheck) {
        jobDescCheck.addEventListener("change", function() {
            document
                .getElementById("jobDescription")
                .classList.toggle("hidden", !this.checked);
        });
    }

    // File Upload
    const pdfUpload = document.getElementById("pdfUpload");
    if (pdfUpload) {
        pdfUpload.addEventListener("change", function(event) {
            const file = event.target.files[0];
            if (file) {
                extractTextFromPDF(file);
            }
        });
    }

    // Generate Button
    const generateBtn = document.getElementById("generateBtn");
    if (generateBtn) {
        generateBtn.addEventListener("click", generateFeedback);
    }
});

function switchTab(type) {
    document
        .getElementById("pdfInput")
        .classList.toggle("hidden", type !== "pdf");
    document
        .getElementById("textInput")
        .classList.toggle("hidden", type !== "text");

    if (type === "pdf") {
        document.getElementById("pdfTab").classList.add("bg-opacity-20");
        document.getElementById("pdfTab").classList.remove("bg-opacity-10");

        document.getElementById("textTab").classList.add("bg-opacity-10");
        document.getElementById("textTab").classList.remove("bg-opacity-20");
    } else {
        document.getElementById("textTab").classList.add("bg-opacity-20");
        document.getElementById("textTab").classList.remove("bg-opacity-10");

        document.getElementById("pdfTab").classList.add("bg-opacity-10");
        document.getElementById("pdfTab").classList.remove("bg-opacity-20");
    }
}

async function extractTextFromPDF(file) {
    document.getElementById("pdfStatus").textContent = "Extracting text...";
    const pdf = await pdfjsLib.getDocument(await file.arrayBuffer()).promise;
    resumeText = "";

    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        resumeText += textContent.items.map((item) => item.str).join(" ") + "\n";
    }

    document.getElementById("pdfStatus").textContent =
        "Text extracted successfully.";
}

async function generateFeedback() {
    const jobRole = document.getElementById("jobRole").value.trim();
    const jobDescription = document.getElementById("jobDescription").value.trim();
    resumeText =
        document.getElementById("resumeText").value.trim() || resumeText;

    if (!resumeText) {
        alert("Please provide your resume text.");
        return;
    }
    if (!jobRole) {
        alert("Please specify the target job role.");
        return;
    }

    const generateBtn = document.getElementById("generateBtn");
    generateBtn.textContent = "Generating...";
    generateBtn.disabled = true;

    try {
        const bodyData = {
            job_role: jobRole,
            job_desc: jobDescription,
            resume_text: resumeText,
        };
        console.log("Sending request to backend:", bodyData);

        // ✅ Localhost only (always points to Flask backend)
        // Use the live Render URL for the deployed service
        const API_BASE = "https://resume-reviewer-project.onrender.com";

        const response = await fetch(`${API_BASE}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyData),
        });

        const data = await response.json();
        console.log("Backend response:", data);

        if (data.feedback) {
            document.getElementById("feedbackContent").innerHTML =
                data.feedback.replace(/\n/g, "<br>");
            document
                .getElementById("feedbackSection")
                .classList.remove("hidden");
        } else {
            alert("Error: " + (data.error || "Unknown backend error"));
        }
    } catch (error) {
        console.error(error);
        alert("Error generating feedback. Backend may not be running.");
    } finally {
        generateBtn.textContent = "Get Feedback";
        generateBtn.disabled = false;
    }
}