// Game state
let currentDiscipline = null;
let currentLevel = 1;
let currentScore = 0;
let currentSequence = [];
let memorizeTime = 0;
let timer = null;

// Load high scores from localStorage
function loadHighScores() {
    const disciplines = ['numbers', 'words', 'cards', 'patterns'];
    disciplines.forEach(discipline => {
        const score = localStorage.getItem(`highscore-${discipline}`) || '-';
        const element = document.getElementById(`hs-${discipline}`);
        if (element) element.textContent = score;
    });
}

// Save high score
function saveHighScore(discipline, score) {
    const currentHigh = parseInt(localStorage.getItem(`highscore-${discipline}`)) || 0;
    if (score > currentHigh) {
        localStorage.setItem(`highscore-${discipline}`, score);
        loadHighScores();
    }
}

// Start a discipline
function startDiscipline(discipline) {
    currentDiscipline = discipline;
    currentLevel = 1;
    currentScore = 0;

    document.getElementById('menu').classList.add('hidden');
    document.getElementById('game').classList.remove('hidden');

    const titles = {
        numbers: 'Sifferminne',
        words: 'Ordminne',
        cards: 'Kortminne',
        patterns: 'Mönsterminne'
    };

    document.getElementById('game-title').textContent = titles[discipline];
    document.getElementById('level').textContent = currentLevel;
    document.getElementById('score').textContent = currentScore;

    startRound();
}

// Start a new round
function startRound() {
    document.getElementById('phase-display').classList.remove('hidden');
    document.getElementById('phase-recall').classList.add('hidden');
    document.getElementById('phase-result').classList.add('hidden');
    document.getElementById('ready-btn').classList.add('hidden');

    const displayArea = document.getElementById('display-area');
    displayArea.innerHTML = '';

    switch(currentDiscipline) {
        case 'numbers':
            startNumbersRound();
            break;
        case 'words':
            startWordsRound();
            break;
        case 'cards':
            startCardsRound();
            break;
        case 'patterns':
            startPatternsRound();
            break;
    }
}

// Numbers discipline
function startNumbersRound() {
    const length = 3 + currentLevel;
    currentSequence = [];

    for (let i = 0; i < length; i++) {
        currentSequence.push(Math.floor(Math.random() * 10));
    }

    const displayArea = document.getElementById('display-area');
    displayArea.textContent = currentSequence.join(' ');

    memorizeTime = Math.min(2000 + length * 1000, 10000);

    setTimeout(() => {
        displayArea.textContent = '...';
        document.getElementById('ready-btn').classList.remove('hidden');
    }, memorizeTime);
}

// Words discipline
function startWordsRound() {
    const wordBank = [
        'äpple', 'banan', 'citron', 'druva', 'fikon',
        'hallon', 'jordgubbe', 'kiwi', 'melon', 'päron',
        'bil', 'cykel', 'tåg', 'båt', 'flygplan',
        'hus', 'träd', 'blomma', 'sten', 'vatten',
        'bok', 'penna', 'dator', 'telefon', 'lampa',
        'stol', 'bord', 'soffa', 'säng', 'kudde',
        'hund', 'katt', 'häst', 'fågel', 'fisk',
        'sol', 'måne', 'stjärna', 'moln', 'regn'
    ];

    const length = 3 + currentLevel;
    currentSequence = [];

    const shuffled = [...wordBank].sort(() => Math.random() - 0.5);
    currentSequence = shuffled.slice(0, length);

    const displayArea = document.getElementById('display-area');
    displayArea.innerHTML = '<div class="word-list">' +
        currentSequence.map((word, i) => `<div class="word-item">${i + 1}. ${word}</div>`).join('') +
        '</div>';

    memorizeTime = Math.min(3000 + length * 1500, 15000);

    setTimeout(() => {
        displayArea.innerHTML = '...';
        document.getElementById('ready-btn').classList.remove('hidden');
    }, memorizeTime);
}

// Cards discipline
function startCardsRound() {
    const suits = ['♠', '♥', '♦', '♣'];
    const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

    const length = 2 + Math.floor(currentLevel / 2) * 2;
    currentSequence = [];

    for (let i = 0; i < length; i++) {
        const suit = suits[Math.floor(Math.random() * suits.length)];
        const rank = ranks[Math.floor(Math.random() * ranks.length)];
        currentSequence.push(rank + suit);
    }

    const displayArea = document.getElementById('display-area');
    displayArea.innerHTML = currentSequence.map(card =>
        `<div class="card">${card}</div>`
    ).join('');

    memorizeTime = Math.min(2000 + length * 1500, 12000);

    setTimeout(() => {
        displayArea.innerHTML = '...';
        document.getElementById('ready-btn').classList.remove('hidden');
    }, memorizeTime);
}

// Patterns discipline
function startPatternsRound() {
    const gridSize = 5;
    const numActive = 3 + currentLevel;
    currentSequence = [];

    const allCells = [];
    for (let i = 0; i < gridSize * gridSize; i++) {
        allCells.push(i);
    }

    const shuffled = allCells.sort(() => Math.random() - 0.5);
    currentSequence = shuffled.slice(0, numActive);

    const displayArea = document.getElementById('display-area');
    let html = '<div class="pattern-grid">';
    for (let i = 0; i < gridSize * gridSize; i++) {
        const isActive = currentSequence.includes(i);
        html += `<div class="pattern-cell ${isActive ? 'active' : ''}" data-index="${i}"></div>`;
    }
    html += '</div>';
    displayArea.innerHTML = html;

    memorizeTime = Math.min(2000 + numActive * 800, 10000);

    setTimeout(() => {
        const cells = displayArea.querySelectorAll('.pattern-cell');
        cells.forEach(cell => cell.classList.remove('active'));
        document.getElementById('ready-btn').classList.remove('hidden');
    }, memorizeTime);
}

// Start recall phase
function startRecall() {
    document.getElementById('phase-display').classList.add('hidden');
    document.getElementById('phase-recall').classList.remove('hidden');

    const recallArea = document.getElementById('recall-area');
    recallArea.innerHTML = '';

    switch(currentDiscipline) {
        case 'numbers':
            recallArea.innerHTML = '<input type="text" id="answer-input" placeholder="Skriv siffrorna (tex: 1 2 3 4)">';
            break;
        case 'words':
            recallArea.innerHTML = '<input type="text" id="answer-input" placeholder="Skriv orden separerade med komma">';
            break;
        case 'cards':
            recallArea.innerHTML = '<input type="text" id="answer-input" placeholder="Skriv korten (tex: A♠ 2♥)">';
            break;
        case 'patterns':
            recallPatterns();
            break;
    }

    if (currentDiscipline !== 'patterns') {
        document.getElementById('answer-input').focus();
    }
}

// Recall for patterns (interactive)
function recallPatterns() {
    const recallArea = document.getElementById('recall-area');
    let html = '<p>Klicka på de rutor som var markerade:</p>';
    html += '<div class="pattern-grid">';
    for (let i = 0; i < 25; i++) {
        html += `<div class="pattern-cell" data-index="${i}" onclick="togglePatternCell(this)"></div>`;
    }
    html += '</div>';
    recallArea.innerHTML = html;
}

function togglePatternCell(cell) {
    cell.classList.toggle('active');
}

// Submit answer
function submitAnswer() {
    let userAnswer = [];
    let correct = false;

    switch(currentDiscipline) {
        case 'numbers':
            const numInput = document.getElementById('answer-input').value;
            userAnswer = numInput.replace(/\s+/g, '').split('').map(n => parseInt(n));
            correct = arraysEqual(userAnswer, currentSequence);
            break;

        case 'words':
            const wordInput = document.getElementById('answer-input').value;
            userAnswer = wordInput.toLowerCase().split(',').map(w => w.trim());
            correct = arraysEqual(userAnswer, currentSequence);
            break;

        case 'cards':
            const cardInput = document.getElementById('answer-input').value;
            userAnswer = cardInput.trim().split(/\s+/);
            correct = arraysEqual(userAnswer, currentSequence);
            break;

        case 'patterns':
            const cells = document.querySelectorAll('#recall-area .pattern-cell.active');
            userAnswer = Array.from(cells).map(cell => parseInt(cell.dataset.index));
            correct = arraysEqual(userAnswer.sort((a,b) => a-b), currentSequence.sort((a,b) => a-b));
            break;
    }

    showResult(correct);
}

// Check if arrays are equal
function arraysEqual(arr1, arr2) {
    if (arr1.length !== arr2.length) return false;
    for (let i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) return false;
    }
    return true;
}

// Show result
function showResult(correct) {
    document.getElementById('phase-recall').classList.add('hidden');
    document.getElementById('phase-result').classList.remove('hidden');

    const resultTitle = document.getElementById('result-title');
    const resultDetails = document.getElementById('result-details');

    if (correct) {
        currentScore += currentLevel * 10;
        currentLevel++;

        resultTitle.innerHTML = '<div class="result-success">✓ Rätt!</div>';
        resultDetails.innerHTML = `
            <p style="font-size: 1.3em; margin-bottom: 10px;">Grattis! Du klarade nivå ${currentLevel - 1}!</p>
            <p>Poäng för denna nivå: ${(currentLevel - 1) * 10}</p>
            <p style="font-size: 1.5em; font-weight: bold; color: #667eea; margin-top: 10px;">
                Total poäng: ${currentScore}
            </p>
        `;

        document.getElementById('score').textContent = currentScore;
        document.getElementById('level').textContent = currentLevel;
    } else {
        resultTitle.innerHTML = '<div class="result-fail">✗ Fel</div>';
        resultDetails.innerHTML = `
            <p style="font-size: 1.3em; margin-bottom: 10px;">Tyvärr fel svar!</p>
            <p>Du nådde nivå: ${currentLevel}</p>
            <p style="font-size: 1.5em; font-weight: bold; color: #667eea; margin-top: 10px;">
                Slutpoäng: ${currentScore}
            </p>
            <p style="margin-top: 15px; color: #666;">Rätt svar var: ${formatAnswer()}</p>
        `;

        saveHighScore(currentDiscipline, currentScore);

        const nextBtn = document.querySelector('#phase-result .btn-primary');
        nextBtn.style.display = 'none';
    }
}

// Format answer for display
function formatAnswer() {
    switch(currentDiscipline) {
        case 'numbers':
            return currentSequence.join(' ');
        case 'words':
            return currentSequence.join(', ');
        case 'cards':
            return currentSequence.join(' ');
        case 'patterns':
            return `Positioner: ${currentSequence.sort((a,b) => a-b).join(', ')}`;
    }
}

// Next round
function nextRound() {
    startRound();
}

// Back to menu
function backToMenu() {
    document.getElementById('game').classList.add('hidden');
    document.getElementById('menu').classList.remove('hidden');
    currentDiscipline = null;
    loadHighScores();
}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    loadHighScores();
});
