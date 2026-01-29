// OVERLAY-FINAL.JS - Lògica completa

// Variables globals
let currentStationIndex = 0;
let rotationInterval = null;
let rotationActive = true; // PER DEFECTE ACTIVA
let animationEnabled = true; // Animació activada per defecte
let blindAnimationActive = true;

// Inicialització
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Overlay meteorològic inicialitzat');
    
    // Configurar nombre d'estacions
    document.getElementById('active-stations-count').textContent = OVERLAY_CONFIG.activeStations.length.toString();
    document.getElementById('total-stations').textContent = OVERLAY_CONFIG.activeStations.length.toString();
    document.getElementById('current-station-display').textContent = OVERLAY_CONFIG.activeStations[0].code;
    
    // Carregar dades de la primera estació (YT)
    loadStationData(OVERLAY_CONFIG.activeStations[0]);
    
    // Iniciar animació de persiana
    startBlindAnimation();
    
    // Actualitzar rellotge amb segons
    updateClock();
    setInterval(updateClock, 1000);
    
    // Actualitzar període semihorari
    updateTimePeriod();
    setInterval(updateTimePeriod, 30000);
    
    // Iniciar rotació automàtica (per defecte activa)
    startStationRotation();
    
    // Actualitzar estat de la rotació
    document.getElementById('rotation-status').textContent = 'ACTIVA';
});

// FUNCIÓ PER INICIAR ANIMACIÓ DE PERSIANA
function startBlindAnimation() {
    if (!blindAnimationActive) return;
    
    const animatedItems = document.querySelectorAll('.animated-item');
    animatedItems.forEach(item => {
        item.style.animationPlayState = 'running';
    });
}

// FUNCIÓ PER REINICIAR ANIMACIÓ DE PERSIANA
function restartBlindAnimation() {
    const animatedItems = document.querySelectorAll('.animated-item');
    
    // Aturar i reiniciar
    animatedItems.forEach(item => {
        item.style.animation = 'none';
    });
    
    // Forçar reflow
    void document.querySelector('.overlay-header').offsetWidth;
    
    // Restaurar animacions
    setTimeout(() => {
        animatedItems.forEach(item => {
            item.style.animation = '';
            item.style.animationPlayState = 'running';
        });
    }, 10);
    
    console.log('🔄 Animació de persiana reiniciada');
    return true;
}

// FUNCIÓ PER ALTERNAR ANIMACIÓ
function toggleBlindAnimation() {
    blindAnimationActive = !blindAnimationActive;
    const animatedItems = document.querySelectorAll('.animated-item');
    
    if (blindAnimationActive) {
        animatedItems.forEach(item => {
            item.style.animationPlayState = 'running';
            item.style.opacity = '1';
        });
        console.log('🎬 Animació ACTIVADA');
    } else {
        animatedItems.forEach(item => {
            item.style.animationPlayState = 'paused';
            item.style.opacity = '1'; // Mantenir visibles
        });
        console.log('⏸️ Animació DESACTIVADA');
    }
    
    return blindAnimationActive;
}

// FUNCIÓ PER ACTUALITZAR RELLOTGE
function updateClock() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const timeString = `HORA (LT): ${hours}:${minutes}:${seconds}`;
    
    // Actualitzar rellotge principal
    document.getElementById('current-time').textContent = timeString;
    
    // Actualitzar hora d'actualització al peu
    document.getElementById('last-update').textContent = `${hours}:${minutes}`;
    document.getElementById('update-time').textContent = `${hours}:${minutes}`;
}

// FUNCIÓ PER CALCULAR PERÍODE SEMIHORARI
function updateTimePeriod() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    
    let periodStartHour = currentHour;
    let periodStartMinute = currentMinute < 30 ? '00' : '30';
    let periodEndHour = currentMinute < 30 ? currentHour : (currentHour + 1) % 24;
    let periodEndMinute = currentMinute < 30 ? '30' : '00';
    
    if (periodEndMinute === '00' && periodEndHour === 0) {
        periodEndHour = 24;
    }
    
    const periodString = `${periodStartHour.toString().padStart(2, '0')}:${periodStartMinute} - ${periodEndHour.toString().padStart(2, '0')}:${periodEndMinute}`;
    document.getElementById('current-period').textContent = periodString;
}

// FUNCIÓ PER CARREGAR DADES D'ESTACIÓ
function loadStationData(station) {
    console.log(`📊 Carregant dades per: ${station.name}`);
    
    // Actualitzar informació de l'estació
    updateStationInfo(station);
    
    // Generar dades simulades
    generateWeatherData(station);
    
    // Carregar dades del dia
    loadDayData(station.code);
    
    // Actualitzar display d'administrador
    document.getElementById('current-station-display').textContent = station.code;
}

// FUNCIÓ PER ACTUALITZAR INFORMACIÓ D'ESTACIÓ
function updateStationInfo(station) {
    document.getElementById('current-station-name').textContent = station.name;
    
    // Extreure municipi
    const municipality = extractMunicipality(station.name);
    document.getElementById('current-municipality').textContent = municipality;
    
    // Determinar comarca
    const comarca = extractComarca(station.code);
    document.getElementById('current-comarca').textContent = comarca;
}

// FUNCIÓ PER EXTREURE MUNICIPI
function extractMunicipality(stationName) {
    const parts = stationName.split(' - ');
    if (parts.length > 1) {
        return parts[0];
    }
    
    const patterns = [
        /^(.*?)\s+-\s+/,
        /^(.*?)\s+\(/,
        /^(.*?)\s+___/
    ];
    
    for (const pattern of patterns) {
        const match = stationName.match(pattern);
        if (match && match[1]) {
            return match[1].trim();
        }
    }
    
    return stationName;
}

// FUNCIÓ PER DETERMINAR COMARCA
function extractComarca(stationCode) {
    const comarcasMap = {
        'YT': 'Pallars Sobirà', 'Z1': 'Pallars Sobirà', 'Z7': 'Pallars Sobirà',
        'DN': 'Selva', 'DJ': 'Pla de l\'Estany',
        'X4': 'Barcelonès', 
        'UN': 'Gironès', 'UO': 'Gironès', 'XJ': 'Gironès',
        'MS': 'Berguedà', 
        'W1': 'Alt Empordà', 'D4': 'Alt Empordà', 'J5': 'Alt Empordà',
        'DP': 'Cerdanya', 'YA': 'Cerdanya', 'Z3': 'Cerdanya',
        'XL': 'Baix Llobregat',
        'YU': 'Osona', 'XO': 'Osona',
        'CD': 'Alt Urgell',
        'Z2': 'Alta Ribagorça',
        'VK': 'Segrià',
        'YB': 'Garrotxa',
        'DG': 'Ripollès', 'CI': 'Ripollès', 'ZC': 'Ripollès',
        'XS': 'Selva',
        'XH': 'Pallars Sobirà',
        'XE': 'Tarragonès',
        'UE': 'Baix Empordà',
        'VS': 'Val d\'Aran',
        'D7': 'Ribera d\'Ebre'
    };
    
    return comarcasMap[stationCode] || 'Comarca desconeguda';
}

// FUNCIÓ PER GENERAR DADES METEOROLÒGIQUES
function generateWeatherData(station) {
    const stationCode = station.code;
    let baseTemp = 15;
    
    // Ajustar temperatura segons l'altura
    const altitudeMatch = station.name.match(/\((\d+(?:\.\d+)?)\s*m\)/);
    if (altitudeMatch) {
        const altitude = parseFloat(altitudeMatch[1]);
        baseTemp -= (altitude / 100) * 0.65;
    }
    
    // Ajustar segons regió
    if (stationCode.startsWith('Z') || stationCode === 'DG' || stationCode === 'CI') {
        baseTemp -= 5; // Muntanya
    }
    
    if (stationCode === 'X4' || stationCode === 'XL' || stationCode === 'XE') {
        baseTemp += 3; // Costanera/urbana
    }
    
    // Generar dades realistes
    const weatherData = {
        tempAvg: (baseTemp + (Math.random() * 4 - 2)).toFixed(1),
        tempMax: (baseTemp + 3 + Math.random() * 3).toFixed(1),
        tempMin: (baseTemp - 3 + Math.random() * 3).toFixed(1),
        humidity: Math.floor(Math.random() * 30 + 50),
        precipitation: (Math.random() * 2).toFixed(1),
        windAvg: (Math.random() * 15 + 5).toFixed(1),
        windDir: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.floor(Math.random() * 8)],
        windGust: (Math.random() * 20 + 10).toFixed(1),
        pressure: Math.floor(Math.random() * 20 + 1000),
        radiation: Math.floor(Math.random() * 400 + 100),
        altitude: altitudeMatch ? altitudeMatch[1] : Math.floor(Math.random() * 1500 + 100).toString()
    };
    
    // Actualitzar la interfície
    document.getElementById('temp-avg').textContent = `${weatherData.tempAvg} °C`;
    document.getElementById('temp-max').textContent = `${weatherData.tempMax} °C`;
    document.getElementById('temp-min').textContent = `${weatherData.tempMin} °C`;
    document.getElementById('humidity').textContent = `${weatherData.humidity} %`;
    document.getElementById('precipitation').textContent = `${weatherData.precipitation} mm`;
    document.getElementById('wind-avg').textContent = `${weatherData.windAvg} km/h`;
    document.getElementById('wind-dir').textContent = weatherData.windDir;
    document.getElementById('wind-gust').textContent = `${weatherData.windGust} km/h`;
    document.getElementById('pressure').textContent = `${weatherData.pressure} hPa`;
    document.getElementById('radiation').textContent = `${weatherData.radiation} W/m²`;
    document.getElementById('altitude').textContent = `${weatherData.altitude} m`;
}

// FUNCIÓ PER CARREGAR DADES DEL DIA
function loadDayData(stationCode) {
    let dayTempMax, dayTempMin;
    
    if (stationCode.startsWith('Z') || stationCode === 'DG' || stationCode === 'CI') {
        dayTempMax = (-5 + Math.random() * 8).toFixed(1);
        dayTempMin = (-10 + Math.random() * 6).toFixed(1);
    } else if (stationCode === 'X4' || stationCode === 'XL' || stationCode === 'XE') {
        dayTempMax = (10 + Math.random() * 8).toFixed(1);
        dayTempMin = (5 + Math.random() * 6).toFixed(1);
    } else {
        dayTempMax = (5 + Math.random() * 10).toFixed(1);
        dayTempMin = (0 + Math.random() * 8).toFixed(1);
    }
    
    const dayPrecipitation = (Math.random() * 3).toFixed(1);
    
    document.getElementById('day-temp-max').textContent = `${dayTempMax}°C`;
    document.getElementById('day-temp-min').textContent = `${dayTempMin}°C`;
    document.getElementById('day-precipitation').textContent = `${dayPrecipitation} mm`;
}

// FUNCIÓ PER ROTAR ESTACIÓ
function rotateStation() {
    const stations = OVERLAY_CONFIG.activeStations;
    if (stations.length === 0) return;
    
    currentStationIndex = (currentStationIndex + 1) % stations.length;
    const station = stations[currentStationIndex];
    
    loadStationData(station);
    
    // Reiniciar animació quan canvïa d'estació
    if (blindAnimationActive) {
        restartBlindAnimation();
    }
    
    console.log(`🔄 Canvi a estació: ${station.displayName}`);
    return station;
}

// FUNCIÓ PER INICIAR ROTACIÓ AUTOMÀTICA
function startStationRotation() {
    if (rotationInterval) {
        clearInterval(rotationInterval);
    }
    
    rotationInterval = setInterval(() => {
        if (rotationActive) {
            rotateStation();
        }
    }, OVERLAY_CONFIG.stationRotationInterval);
}

// FUNCIÓ PER ALTERNAR ROTACIÓ
function toggleStationRotation(active) {
    rotationActive = active !== undefined ? active : !rotationActive;
    
    if (rotationActive) {
        startStationRotation();
        console.log('🔄 Rotació automàtica ACTIVADA');
        document.getElementById('rotation-status').textContent = 'ACTIVA';
    } else {
        if (rotationInterval) {
            clearInterval(rotationInterval);
            rotationInterval = null;
        }
        console.log('⏸️ Rotació automàtica DESACTIVADA');
        document.getElementById('rotation-status').textContent = 'INACTIVA';
    }
    
    return rotationActive;
}

// FUNCIÓ PER CANVIAR INTERVAL DE ROTACIÓ
function setRotationInterval(intervalMs) {
    OVERLAY_CONFIG.stationRotationInterval = intervalMs;
    
    if (rotationActive && rotationInterval) {
        clearInterval(rotationInterval);
        startStationRotation();
    }
    
    console.log(`⏱️ Interval de rotació canviat a: ${intervalMs/1000} segons`);
}

// FUNCIÓ PER ACTUALITZAR TOTES LES DADES
function updateWeatherData() {
    const currentStation = OVERLAY_CONFIG.activeStations[currentStationIndex];
    loadStationData(currentStation);
    console.log('🔄 Dades actualitzades');
}

// Exportar funcions per als controls
window.rotateStation = rotateStation;
window.toggleStationRotation = toggleStationRotation;
window.setRotationInterval = setRotationInterval;
window.updateWeatherData = updateWeatherData;
window.updateClock = updateClock;
window.restartBlindAnimation = restartBlindAnimation;
window.toggleBlindAnimation = toggleBlindAnimation;