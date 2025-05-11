// Mesh Radio Simulation Dashboard

// Canvas and rendering variables
const canvas = document.getElementById('simulation-canvas');
const ctx = canvas.getContext('2d');
let animationFrameId;
let simulationState = {};
let isRunning = false;

// UI elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');
const togglePanelBtn = document.getElementById('toggle-panel');
const sidePanel = document.querySelector('.side-panel');
const stepCounter = document.getElementById('step-counter');
const tankCounter = document.getElementById('tank-counter');
const linkCounter = document.getElementById('link-counter');
const connectionStatus = document.getElementById('connection-status');
const applyParamsBtn = document.getElementById('apply-params');
const killRandomTankBtn = document.getElementById('kill-random-tank');

// Parameters inputs
const nbTanksInput = document.getElementById('nb-tanks');
const maxStepSizeInput = document.getElementById('max-step-size');
const sigmaXInput = document.getElementById('sigma-x');
const sigmaYInput = document.getElementById('sigma-y');

// Constants
const TANK_RADIUS = 6;
const HQ_SIZE = 12;
const TARGET_SIZE = 8;
const GRID_SIZE = 20;
const BACKGROUND_PATTERN_SIZE = 5;

// Colors
const COLORS = {
    tank: '#48cae4',
    hq: '#ffd700',
    target: '#f44336',
    link: 'rgba(255, 255, 255, 0.4)',
    grid: 'rgba(255, 255, 255, 0.05)',
    background: '#0d1b2a',
    terrain: [
        'rgba(13, 27, 42, 0.7)',   // Darkest (lowest altitude)
        'rgba(27, 38, 59, 0.7)',
        'rgba(65, 90, 119, 0.7)',
        'rgba(119, 141, 169, 0.7)',
        'rgba(224, 225, 221, 0.7)'  // Lightest (highest altitude)
    ]
};

// Initialize the dashboard
function init() {
    // Set canvas size
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Event listeners
    startBtn.addEventListener('click', startSimulation);
    stopBtn.addEventListener('click', stopSimulation);
    resetBtn.addEventListener('click', resetSimulation);
    togglePanelBtn.addEventListener('click', togglePanel);
    applyParamsBtn.addEventListener('click', applyParameters);
    killRandomTankBtn.addEventListener('click', killRandomTank);
    
    // Start fetching simulation state
    fetchSimulationState();
    
    // Initial render
    render();
}

// Resize canvas to fit container
function resizeCanvas() {
    const container = document.querySelector('.simulation-container');
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    render();
}

// Toggle side panel
function togglePanel() {
    sidePanel.classList.toggle('collapsed');
}

// Fetch simulation state from API
async function fetchSimulationState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        
        simulationState = data.state;
        isRunning = data.running;
        
        // Update UI
        stepCounter.textContent = data.step;
        if (simulationState.tanks) {
            tankCounter.textContent = simulationState.tanks.length;
        }
        if (simulationState.links) {
            linkCounter.textContent = simulationState.links.length;
        }
        
        connectionStatus.textContent = 'CONNECTED';
        connectionStatus.classList.remove('disconnected');
        
        // Schedule next fetch if running
        setTimeout(fetchSimulationState, 100);
        
        // Render the updated state
        render();
    } catch (error) {
        console.error('Error fetching simulation state:', error);
        connectionStatus.textContent = 'DISCONNECTED';
        connectionStatus.classList.add('disconnected');
        
        // Retry after a delay
        setTimeout(fetchSimulationState, 2000);
    }
}

// Start simulation
async function startSimulation() {
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        isRunning = true;
    } catch (error) {
        console.error('Error starting simulation:', error);
    }
}

// Stop simulation
async function stopSimulation() {
    try {
        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        isRunning = false;
    } catch (error) {
        console.error('Error stopping simulation:', error);
    }
}

// Reset simulation
async function resetSimulation() {
    try {
        const response = await fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Reset counters
        stepCounter.textContent = '0';
    } catch (error) {
        console.error('Error resetting simulation:', error);
    }
}

// Apply parameter changes
async function applyParameters() {
    try {
        const params = {
            nb_tanks: parseInt(nbTanksInput.value),
            max_step_size: parseFloat(maxStepSizeInput.value),
            sigmas: [parseInt(sigmaXInput.value), parseInt(sigmaYInput.value)]
        };
        
        const response = await fetch('/api/params', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
    } catch (error) {
        console.error('Error applying parameters:', error);
    }
}

// Kill a random tank
async function killRandomTank() {
    if (!simulationState.tanks || simulationState.tanks.length === 0) {
        return;
    }
    
    try {
        const randomIndex = Math.floor(Math.random() * simulationState.tanks.length);
        const tankIdx = simulationState.tanks[randomIndex].idx;
        
        const response = await fetch('/api/kill_tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tank_idx: tankIdx })
        });
    } catch (error) {
        console.error('Error killing tank:', error);
    }
}

// Render the simulation
function render() {
    if (!canvas || !ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background pattern
    drawBackgroundPattern();
    
    if (!simulationState || !simulationState.map_size) {
        // Draw loading message if no state
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '16px "Roboto Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Loading simulation...', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    // Calculate scale to fit the map in the canvas
    const scale = Math.min(
        canvas.width / simulationState.map_size[0],
        canvas.height / simulationState.map_size[1]
    ) * 0.9;
    
    // Calculate offset to center the map
    const offsetX = (canvas.width - simulationState.map_size[0] * scale) / 2;
    const offsetY = (canvas.height - simulationState.map_size[1] * scale) / 2;
    
    // Draw terrain
    if (simulationState.altitude) {
        drawTerrain(scale, offsetX, offsetY);
    }
    
    // Draw links between tanks
    if (simulationState.links) {
        drawLinks(scale, offsetX, offsetY);
    }
    
    // Draw HQ
    if (simulationState.hq) {
        drawHQ(scale, offsetX, offsetY);
    }
    
    // Draw targets
    if (simulationState.targets) {
        drawTargets(scale, offsetX, offsetY);
    }
    
    // Draw tanks
    if (simulationState.tanks) {
        drawTanks(scale, offsetX, offsetY);
    }
    
    // Request next frame
    animationFrameId = requestAnimationFrame(render);
}

// Draw background pattern of small crosses or dashes
function drawBackgroundPattern() {
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    
    // Draw small crosses pattern
    for (let x = 0; x < canvas.width; x += GRID_SIZE) {
        for (let y = 0; y < canvas.height; y += GRID_SIZE) {
            // Draw a small cross
            const size = BACKGROUND_PATTERN_SIZE / 2;
            
            ctx.beginPath();
            ctx.moveTo(x - size, y);
            ctx.lineTo(x + size, y);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(x, y - size);
            ctx.lineTo(x, y + size);
            ctx.stroke();
        }
    }
}

// Draw terrain based on altitude
function drawTerrain(scale, offsetX, offsetY) {
    const altitude = simulationState.altitude;
    const width = simulationState.map_size[0];
    const height = simulationState.map_size[1];
    
    // Find min and max altitude for normalization
    let minAlt = Infinity;
    let maxAlt = -Infinity;
    
    for (let x = 0; x < width; x++) {
        for (let y = 0; y < height; y++) {
            const alt = altitude[x][y];
            minAlt = Math.min(minAlt, alt);
            maxAlt = Math.max(maxAlt, alt);
        }
    }
    
    // Draw terrain with color based on altitude
    const cellSize = scale;
    
    for (let x = 0; x < width; x += 5) {
        for (let y = 0; y < height; y += 5) {
            const alt = altitude[x][y];
            const normalizedAlt = (alt - minAlt) / (maxAlt - minAlt);
            
            // Get color based on normalized altitude
            const colorIndex = Math.min(
                Math.floor(normalizedAlt * COLORS.terrain.length),
                COLORS.terrain.length - 1
            );
            
            ctx.fillStyle = COLORS.terrain[colorIndex];
            ctx.fillRect(
                offsetX + x * scale,
                offsetY + y * scale,
                cellSize * 5,
                cellSize * 5
            );
        }
    }
}

// Draw links between tanks
function drawLinks(scale, offsetX, offsetY) {
    ctx.strokeStyle = COLORS.link;
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 3]);
    
    for (const [i, j] of simulationState.links) {
        const tank1 = simulationState.tanks[i];
        const tank2 = simulationState.tanks[j];
        
        if (tank1 && tank2) {
            ctx.beginPath();
            ctx.moveTo(
                offsetX + tank1.pos[0] * scale,
                offsetY + tank1.pos[1] * scale
            );
            ctx.lineTo(
                offsetX + tank2.pos[0] * scale,
                offsetY + tank2.pos[1] * scale
            );
            ctx.stroke();
        }
    }
    
    ctx.setLineDash([]);
}

// Draw HQ
function drawHQ(scale, offsetX, offsetY) {
    const [x, y] = simulationState.hq;
    
    // Draw star for HQ
    ctx.fillStyle = COLORS.hq;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    
    const centerX = offsetX + x * scale;
    const centerY = offsetY + y * scale;
    const size = HQ_SIZE;
    
    drawStar(centerX, centerY, 5, size, size / 2);
}

// Draw targets
function drawTargets(scale, offsetX, offsetY) {
    ctx.fillStyle = COLORS.target;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    
    for (const [x, y] of simulationState.targets) {
        const centerX = offsetX + x * scale;
        const centerY = offsetY + y * scale;
        
        // Draw X mark
        ctx.beginPath();
        ctx.moveTo(centerX - TARGET_SIZE / 2, centerY - TARGET_SIZE / 2);
        ctx.lineTo(centerX + TARGET_SIZE / 2, centerY + TARGET_SIZE / 2);
        ctx.moveTo(centerX + TARGET_SIZE / 2, centerY - TARGET_SIZE / 2);
        ctx.lineTo(centerX - TARGET_SIZE / 2, centerY + TARGET_SIZE / 2);
        ctx.stroke();
        
        // Draw circle around X
        ctx.beginPath();
        ctx.arc(centerX, centerY, TARGET_SIZE, 0, Math.PI * 2);
        ctx.stroke();
    }
}

// Draw tanks
function drawTanks(scale, offsetX, offsetY) {
    for (const tank of simulationState.tanks) {
        const [x, y] = tank.pos;
        const centerX = offsetX + x * scale;
        const centerY = offsetY + y * scale;
        
        // Draw tank circle
        ctx.fillStyle = COLORS.tank;
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, TANK_RADIUS, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        
        // Draw tank ID
        ctx.fillStyle = '#000';
        ctx.font = '10px "Roboto Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(tank.idx.toString(), centerX, centerY);
    }
}

// Helper function to draw a star
function drawStar(cx, cy, spikes, outerRadius, innerRadius) {
    let rot = Math.PI / 2 * 3;
    let x = cx;
    let y = cy;
    let step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    
    for (let i = 0; i < spikes; i++) {
        x = cx + Math.cos(rot) * outerRadius;
        y = cy + Math.sin(rot) * outerRadius;
        ctx.lineTo(x, y);
        rot += step;

        x = cx + Math.cos(rot) * innerRadius;
        y = cy + Math.sin(rot) * innerRadius;
        ctx.lineTo(x, y);
        rot += step;
    }
    
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
}

// Initialize on page load
window.addEventListener('load', init);
