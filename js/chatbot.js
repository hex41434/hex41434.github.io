(function () {
    'use strict';

    var launcher = document.querySelector('[data-chatbot-launcher]');
    var panel = document.querySelector('[data-chatbot-panel]');
    var closeButton = document.querySelector('[data-chatbot-close]');
    var form = document.querySelector('[data-chatbot-form]');
    var input = document.querySelector('[data-chatbot-input]');
    var messages = document.querySelector('[data-chatbot-messages]');

    if (!launcher || !panel || !closeButton || !form || !input || !messages) {
        return;
    }

    var isLocalPreview = window.location.protocol === 'file:'
        || window.location.hostname === 'localhost'
        || window.location.hostname === '127.0.0.1';
    var localApiUrl = isLocalPreview
        ? 'http://127.0.0.1:8000/api/chat'
        : '';
    var apiUrl = window.AIDA_CHATBOT_API_URL || localApiUrl;
    var isBusy = false;

    function appendMessage(text, role) {
        var message = document.createElement('div');
        message.className = 'chatbot-message ' + role;
        message.textContent = text;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
        return message;
    }

    function setOpen(isOpen) {
        panel.classList.toggle('is-open', isOpen);
        launcher.setAttribute('aria-expanded', String(isOpen));

        if (isOpen) {
            input.focus();
        }
    }

    function setBusy(nextBusy) {
        isBusy = nextBusy;
        input.disabled = nextBusy;
        form.querySelector('[data-chatbot-send]').disabled = nextBusy;
    }

    launcher.addEventListener('click', function () {
        setOpen(!panel.classList.contains('is-open'));
    });

    closeButton.addEventListener('click', function () {
        setOpen(false);
        launcher.focus();
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        if (isBusy) {
            return;
        }

        var question = input.value.trim();
        if (!question) {
            return;
        }

        appendMessage(question, 'user');
        input.value = '';

        if (!apiUrl) {
            appendMessage('The chatbot backend is not configured yet. Please set window.AIDA_CHATBOT_API_URL to the HTTPS endpoint of the VPS chatbot API.', 'error');
            return;
        }

        setBusy(true);
        var statusMessage = appendMessage('Thinking...', 'bot status');

        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: question })
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Backend returned HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                statusMessage.textContent = data.answer || 'I could not generate an answer from the available profile context.';
            })
            .catch(function () {
                statusMessage.className = 'chatbot-message error';
                statusMessage.textContent = 'The chatbot is currently unavailable. You can still contact Aida by email or use the CV and profile links on this page.';
            })
            .finally(function () {
                setBusy(false);
                input.focus();
            });
    });
}());
