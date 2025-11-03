// Main JavaScript for simulation form and progress tracking

let currentSimulationId = null;
let progressInterval = null;

document.getElementById('simulationForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Get form values
    const objective = document.getElementById('objective').value;
    const aiProfile = document.getElementById('aiProfile').value;
    const numSims = parseInt(document.getElementById('numSims').value);
    const visualize = document.getElementById('visualize').checked;

    // Validate
    if (!objective) {
        alert('Please select an objective');
        return;
    }

    if (numSims < 1 || numSims > 10000) {
        alert('Number of simulations must be between 1 and 10,000');
        return;
    }

    // Disable form
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Starting...';
    submitBtn.classList.add('opacity-50', 'cursor-not-allowed');

    try {
        // Start simulation
        const response = await fetch('/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                objective_id: objective,
                ai_profile: aiProfile,
                num_simulations: numSims,
                generate_visualizations: visualize
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start simulation');
        }

        const data = await response.json();
        currentSimulationId = data.simulation_id;

        // Show progress section
        document.getElementById('progressSection').classList.remove('hidden');

        // Start polling for progress
        startProgressPolling();

    } catch (error) {
        console.error('Error starting simulation:', error);
        alert(`Error: ${error.message}`);

        // Re-enable form
        submitBtn.disabled = false;
        submitBtn.textContent = 'Run Simulation';
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
});

function startProgressPolling() {
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentSimulationId}`);
            if (!response.ok) {
                throw new Error('Failed to get status');
            }

            const status = await response.json();

            // Update progress UI
            document.getElementById('progressMessage').textContent = status.message;
            document.getElementById('progressPercent').textContent = `${status.progress}%`;
            document.getElementById('progressBar').style.width = `${status.progress}%`;

            // Check if completed
            if (status.status === 'completed') {
                clearInterval(progressInterval);
                // Redirect to results page
                window.location.href = `/results/${currentSimulationId}/view`;
            } else if (status.status === 'error') {
                clearInterval(progressInterval);
                alert(`Simulation failed: ${status.message}`);

                // Re-enable form
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Run Simulation';
                submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');

                // Hide progress section
                document.getElementById('progressSection').classList.add('hidden');
            }

        } catch (error) {
            console.error('Error polling status:', error);
            clearInterval(progressInterval);
            alert('Lost connection to simulation. Please refresh the page.');
        }
    }, 500); // Poll every 500ms
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
});
