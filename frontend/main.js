document.addEventListener('DOMContentLoaded', () => {
    const riskGameSection = document.getElementById('risk-game');
    const questionArea = document.getElementById('risk-question-area');
    const optionsArea = document.getElementById('risk-options-area');
    const feedbackArea = document.getElementById('risk-feedback-area');
    const progressArea = document.getElementById('risk-progress-area');
    const resultsArea = document.getElementById('results-area');
    const riskScoreDisplay = document.getElementById('risk-score-display');

    const riskScenarios = [
        { id: 1, safeText: "Option A: Get 10 dollars for sure.", riskyText: "Option B: 50% chance of 30 dollars, 50% chance of 0 dollars.", nudge: "Let's get started! Which one calls to you?" },
        { id: 2, safeText: "Option A: Get 15 dollars for sure.", riskyText: "Option B: 50% chance of 30 dollars, 50% chance of 0 dollars.", nudge: "Interesting choice! Here's the next one." },
        { id: 3, safeText: "Option A: Get 20 dollars for sure.", riskyText: "Option B: 50% chance of 40 dollars, 50% chance of 0 dollars.", nudge: "You're doing great! Keep it up." },
        { id: 4, safeText: "Option A: Get 25 dollars for sure.", riskyText: "Option B: 50% chance of 40 dollars, 50% chance of 0 dollars.", nudge: "Thinking carefully? Good strategy!" },
        { id: 5, safeText: "Option A: Get 30 dollars for sure.", riskyText: "Option B: 50% chance of 50 dollars, 50% chance of 0 dollars.", nudge: "Halfway there! What's your feeling now?" },
        { id: 6, safeText: "Option A: Get 35 dollars for sure.", riskyText: "Option B: 50% chance of 50 dollars, 50% chance of 0 dollars.", nudge: "This one might make you pause..." },
        { id: 7, safeText: "Option A: Get 40 dollars for sure.", riskyText: "Option B: 50% chance of 60 dollars, 50% chance of 0 dollars.", nudge: "The stakes are shifting. What's your pick?" },
        { id: 8, safeText: "Option A: Get 45 dollars for sure.", riskyText: "Option B: 50% chance of 60 dollars, 50% chance of 0 dollars.", nudge: "Getting trickier? Trust your judgment." },
        { id: 9, safeText: "Option A: Get 50 dollars for sure.", riskyText: "Option B: 50% chance of 70 dollars, 50% chance of 0 dollars.", nudge: "Just a couple more to go!" },
        { id: 10, safeText: "Option A: Get 55 dollars for sure.", riskyText: "Option B: 50% chance of 70 dollars, 50% chance of 0 dollars.", nudge: "Last one! Make it count." }
    ];

    let currentRiskRound = 0;
    const riskUserChoices = [];

    function loadRiskQuestion() {
        const scenario = riskScenarios[currentRiskRound];
        progressArea.textContent = `Round ${scenario.id} of ${riskScenarios.length}`;
        questionArea.innerHTML = `<h3>Round ${scenario.id}</h3>`;

        optionsArea.innerHTML = `
            <button class="choice-button" data-choice="safe">${scenario.safeText}</button>
            <button class="choice-button" data-choice="risky">${scenario.riskyText}</button>
        `;
        feedbackArea.textContent = scenario.nudge;

        optionsArea.querySelectorAll('.choice-button').forEach(button => {
            button.addEventListener('click', handleRiskChoice);
        });
    }

    function handleRiskChoice(event) {
        const choice = event.target.dataset.choice;
        riskUserChoices.push(choice);
        currentRiskRound++;

        optionsArea.querySelectorAll('.choice-button').forEach(button => button.disabled = true);

        if (currentRiskRound < riskScenarios.length) {
            feedbackArea.textContent = `You chose ${choice}. Preparing next round...`;
            setTimeout(loadRiskQuestion, 750);
        } else {
            feedbackArea.textContent = `You chose ${choice}. All rounds completed!`;
            setTimeout(() => {
                finishRiskGame().then(() => { console.log("Risk game submission process finished.") });
            }, 750);
        }
    }

    async function finishRiskGame() {
        questionArea.innerHTML = "<p>Calculating your style...</p>";
        optionsArea.innerHTML = "";
        progressArea.textContent = "";

        const payload = {
            game: "risk",
            choices: riskUserChoices
        };

        console.log("Sending payload:", JSON.stringify(payload));

        try {
            const response = await fetch('http://localhost:8000/game_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const resultData = await response.json();

            if (!response.ok) {
                const errorDetail = resultData.detail ? JSON.stringify(resultData.detail) : `Server error: ${response.status}`;
                console.error('Server validation error:', errorDetail);
                throw new Error(`Validation failed: ${errorDetail}`);
            }

            riskGameSection.style.display = 'none';
            resultsArea.style.display = 'block';
            riskScoreDisplay.textContent = parseFloat(resultData.risk_score).toFixed(3);
            feedbackArea.textContent = "Results displayed!";
        } catch (error) {
            console.error('Error submitting risk choices:', error);
            feedbackArea.textContent = `Error: ${error.message}. Please check console and try again.`;
        }
    }

    if (riskGameSection) {
        loadRiskQuestion();
    }
});