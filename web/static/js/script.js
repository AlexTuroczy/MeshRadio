// Mesh Radio Simulation Dashboard

// Canvas and rendering variables
const canvas = document.getElementById('simulation-canvas');
const ctx = canvas.getContext('2d');
let animationFrameId;
let simulationState = {};
let isRunning = false;
let config = null;

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

// Default constants (will be overridden by config)
let TANK_RADIUS = 10;
let HQ_SIZE = 12;
let TARGET_SIZE = 8;
let GRID_SIZE = 20;
const BACKGROUND_PATTERN_SIZE = 5;

// Tank image
const tankImage = new Image();
tankImage.src = '/static/images/tankconnected.png';

// HQ and target icons (using Font Awesome style)
const HQ_ICON = 'M';  // Will be drawn as a hexagon
const TARGET_ICON = 'T';  // Will be drawn as a diamond

// Default colors (will be overridden by config)
let COLORS = {
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
async function init() {
    // Load configuration
    await loadConfig();
    
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
    
    // Initialize parameter inputs with config values
    updateParameterInputs();
    
    // Start fetching simulation state
    fetchSimulationState();
    
    // Initial render
    render();
}

// Load shared configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        config = await response.json();
        
        // Update constants from config
        if (config.visual) {
            TANK_RADIUS = config.visual.tank_radius;
            HQ_SIZE = config.visual.hq_size;
            TARGET_SIZE = config.visual.target_size;
            GRID_SIZE = config.visual.grid_size;
            
            // Update colors
            if (config.visual.colors) {
                Object.assign(COLORS, config.visual.colors);
            }
        }
        
        console.log('Configuration loaded:', config);
    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

// Update parameter inputs with values from config
function updateParameterInputs() {
    if (config && config.simulation) {
        nbTanksInput.value = config.simulation.nb_tanks;
        maxStepSizeInput.value = config.simulation.max_step_size;
        
        if (config.simulation.sigmas && config.simulation.sigmas.length >= 2) {
            sigmaXInput.value = config.simulation.sigmas[0];
            sigmaYInput.value = config.simulation.sigmas[1];
        }
    }
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
    // Toggle the collapsed class
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
        
        // Update config with new values
        if (config && config.simulation) {
            config.simulation.nb_tanks = params.nb_tanks;
            config.simulation.max_step_size = params.max_step_size;
            config.simulation.sigmas = params.sigmas;
        }
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

// Draw background pattern - tactical grid with terrain features
function drawBackgroundPattern() {
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid lines
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    
    // Draw horizontal and vertical grid lines
    for (let x = 0; x < canvas.width; x += GRID_SIZE) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    
    for (let y = 0; y < canvas.height; y += GRID_SIZE) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
    
    // Add some tactical terrain features (small dots/markers)
    ctx.fillStyle = COLORS.grid;
    
    // Create a sparse pattern of terrain markers
    for (let x = GRID_SIZE; x < canvas.width; x += GRID_SIZE * 3) {
        for (let y = GRID_SIZE; y < canvas.height; y += GRID_SIZE * 3) {
            // Add some randomness to the pattern
            if (Math.random() > 0.7) {
                // Draw a small terrain feature (dot or small shape)
                ctx.beginPath();
                ctx.arc(x + (Math.random() * GRID_SIZE - GRID_SIZE/2), 
                         y + (Math.random() * GRID_SIZE - GRID_SIZE/2), 
                         1, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }
}

// Draw terrain features instead of altitude heatmap
function drawTerrain(scale, offsetX, offsetY) {
    const width = simulationState.map_size[0];
    const height = simulationState.map_size[1];
    
    // Draw tactical terrain features
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 0.5;
    
    // Draw contour-like lines for a tactical map feel
    for (let i = 0; i < 10; i++) {
        const radius = (Math.min(width, height) / 2) * (0.3 + i * 0.07) * scale;
        const centerX = offsetX + width * scale / 2;
        const centerY = offsetY + height * scale / 2;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();
    }
    
    // Add some tactical markers
    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    
    // Create a sparse pattern of terrain markers
    const markerSize = 2;
    for (let x = 0; x < width; x += 10) {
        for (let y = 0; y < height; y += 10) {
            // Add some randomness to the pattern
            if (Math.random() > 0.8) {
                const markerX = offsetX + x * scale;
                const markerY = offsetY + y * scale;
                
                // Draw a small terrain feature (dot or small shape)
                ctx.beginPath();
                ctx.arc(markerX, markerY, markerSize, 0, Math.PI * 2);
                ctx.fill();
            }
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
    
    // Draw hexagon for HQ (modern military command post symbol)
    ctx.fillStyle = COLORS.hq;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    
    const centerX = offsetX + x * scale;
    const centerY = offsetY + y * scale;
    const size = HQ_SIZE;
    
    drawHexagon(centerX, centerY, size);
    
    // Add a small indicator in the center
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(centerX, centerY, size/4, 0, Math.PI * 2);
    ctx.fill();
}

// Helper function to draw a hexagon
function drawHexagon(cx, cy, size) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i;
        const x = cx + size * Math.cos(angle);
        const y = cy + size * Math.sin(angle);
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
}

// Draw targets
function drawTargets(scale, offsetX, offsetY) {
    ctx.fillStyle = COLORS.target;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    
    for (const [x, y] of simulationState.targets) {
        const centerX = offsetX + x * scale;
        const centerY = offsetY + y * scale;
        
        // Draw diamond (rhombus) for target
        drawDiamond(centerX, centerY, TARGET_SIZE);
    }
}

// Helper function to draw a diamond (rhombus)
function drawDiamond(cx, cy, size) {
    ctx.beginPath();
    ctx.moveTo(cx, cy - size);
    ctx.lineTo(cx + size, cy);
    ctx.lineTo(cx, cy + size);
    ctx.lineTo(cx - size, cy);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    
    // Add a small indicator in the center
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx, cy, size/4, 0, Math.PI * 2);
    ctx.fill();
}

// Draw tanks
function drawTanks(scale, offsetX, offsetY) {
    for (const tank of simulationState.tanks) {
        const [x, y] = tank.pos;
        const centerX = offsetX + x * scale;
        const centerY = offsetY + y * scale;
        
        // Draw tank image
        const imgSize = TANK_RADIUS * 2;
        ctx.drawImage(
            tankImage, 
            centerX - imgSize/2, 
            centerY - imgSize/2, 
            imgSize, 
            imgSize
        );
        
        // Draw tank ID next to the tank
        ctx.fillStyle = COLORS.tank;
        ctx.font = 'bold 10px "Roboto Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(tank.idx.toString(), centerX, centerY - imgSize/2 - 8);
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
