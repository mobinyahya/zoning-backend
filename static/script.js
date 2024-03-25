function setupSlider(sliderId, displayId, valuesMap) {
    const slider = document.getElementById(sliderId);
    const displayValue = document.getElementById(displayId);

    slider.oninput = function() {
        displayValue.textContent = valuesMap[this.value];
    };

    // Initialize the displayed value
    displayValue.textContent = valuesMap[slider.value];
}

// Setup for each slider
setupSlider("zoneSlider", "zoneValue", [2, 6, 10, 14, 18]);
setupSlider("shortageSlider", "shortageValue", [10, 20, 30, 40, 50]);
setupSlider("deviationSlider", "deviationValue", [10, 20, 30, 40, 50]);