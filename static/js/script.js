document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript Loaded!");

    let button = document.getElementById("predict-button");
    if (button) {
        button.addEventListener("click", function () {
            alert("Prediction process started!");
        });
    }
});