document.addEventListener("DOMContentLoaded", function () {

    const fileInput = document.getElementById("file");
    const previewImg = document.getElementById("image-preview");
    const uploadForm = document.getElementById("uploadForm");
    const submitBtn = document.getElementById("submitBtn");
    const loadingDiv = document.getElementById("loading");

    // 1. Show image preview when file is selected
    fileInput.onchange = evt => {
        const [file] = fileInput.files;
        if (file) {
            previewImg.src = URL.createObjectURL(file);
            previewImg.style.display = "block";
        }
    };

    // 2. Show loading spinner on submit
    uploadForm.onsubmit = () => {
        submitBtn.style.display = "none"; // Hide button
        loadingDiv.style.display = "block"; // Show spinner

        // Optional: Update text occasionally
        setTimeout(() => {
            document.querySelector("#loading p").innerText = "Detecting objects...";
        }, 2000);
    };

    // 3. Show loading spinner for Detect Live button
    const detectLiveBtn = document.querySelector('a[href*="detect-live"]');
    if (detectLiveBtn) {
        detectLiveBtn.addEventListener("click", function (e) {
            // No e.preventDefault() as we want the navigation to happen
            // Just show the loading state
            const actionButtons = document.querySelector(".action-buttons");
            if (actionButtons) actionButtons.style.display = "none";
            submitBtn.style.display = "none";
            loadingDiv.style.display = "block";
            document.querySelector("#loading p").innerText = "Connecting to ESP32 CAM...";
        });
    }

});