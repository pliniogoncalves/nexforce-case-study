document.addEventListener('DOMContentLoaded', () => {
    const teachButton = document.getElementById('teachAgentBtn');
    const askButton = document.getElementById('askQuestionBtn');

    if(teachButton) teachButton.addEventListener('click', addKnowledge);
    if(askButton) askButton.addEventListener('click', askQuestion);
});

const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000/api'
    : '/api';
    
async function addKnowledge() {
    const urlInput = document.getElementById('knowledgeUrl');
    const statusDiv = document.getElementById('teachStatus');
    const url = urlInput.value;

    if (!url) {
        statusDiv.innerText = "Por favor, insira uma URL.";
        return;
    }

    statusDiv.innerText = "Processando... Isso pode levar até um minuto.";

    try {
        const response = await fetch(`${API_BASE_URL}/add-knowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const result = await response.json();
        if (!response.ok) { throw new Error(result.detail || 'Ocorreu um erro.'); }
        statusDiv.innerText = result.message;
        urlInput.value = "";
    } catch (error) {
        statusDiv.innerText = "Erro: " + error.message;
    }
}

async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const answerDiv = document.getElementById('answerDisplay');
    const question = questionInput.value;

    if (!question) {
        answerDiv.innerText = "Por favor, faça uma pergunta.";
        return;
    }

    const n8nWebhookUrl = 'https://pliniogoncalves.app.n8n.cloud/webhook/f5c0cb34-288f-46b9-9920-2c39f43dd6e6';
    
    answerDiv.innerText = "Pensando...";

    try {
        const finalUrl = `${n8nWebhookUrl}?question=${encodeURIComponent(question)}`;
        const response = await fetch(finalUrl);
        if (!response.ok) { throw new Error(`Erro na rede: ${response.statusText}`); }
        const answer = await response.text();
        answerDiv.innerText = answer;
    } catch (error) {
        answerDiv.innerText = "Erro ao buscar resposta: " + error.message;
    }
}