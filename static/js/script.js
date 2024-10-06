document.addEventListener('DOMContentLoaded', () => {
    const subscribeForm = document.getElementById('subscribe-form');
    const emailInput = document.getElementById('email-input');
    const subscribeButton = document.getElementById('subscribe-button');
    const messageDiv = document.getElementById('message');

    subscribeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = emailInput.value.trim();

        if (!email) {
            showMessage('Please enter a valid email address.', 'text-red-500');
            return;
        }

        subscribeButton.disabled = true;
        subscribeButton.innerText = 'Subscribing...';

        try {
            const response = await fetch('/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `email=${encodeURIComponent(email)}`,
            });

            const data = await response.json();

            if (data.success) {
                showMessage(data.message, 'text-green-500');
                emailInput.value = '';
            } else {
                showMessage(data.message, 'text-red-500');
            }
        } catch (error) {
            showMessage('An error occurred. Please try again later.', 'text-red-500');
        } finally {
            subscribeButton.disabled = false;
            subscribeButton.innerText = 'Subscribe';
        }
    });

    function showMessage(text, className) {
        messageDiv.textContent = text;
        messageDiv.className = `mt-2 text-sm ${className}`;
    }

    // Countdown timer
    const countdownElement = document.getElementById('countdown');
    const launchDate = new Date('2024-12-31T23:59:59').getTime();

    function updateCountdown() {
        const now = new Date().getTime();
        const distance = launchDate - now;

        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        countdownElement.innerHTML = `
            <span>${days}d</span>
            <span>${hours}h</span>
            <span>${minutes}m</span>
            <span>${seconds}s</span>
        `;

        if (distance < 0) {
            clearInterval(countdownInterval);
            countdownElement.innerHTML = '<span>Lynq is now live!</span>';
        }
    }

    const countdownInterval = setInterval(updateCountdown, 1000);
    updateCountdown();

    // Language switching functionality
    let currentLanguage = 'en';
    let translations = {};

    async function loadTranslations(lang) {
        const response = await fetch(`/static/locales/${lang}.json`);
        translations = await response.json();
    }

    function updateContent() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = translations[key] || key;
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = translations[key] || key;
        });

        document.documentElement.lang = currentLanguage;
    }

    function changeLanguage(lang) {
        if (lang === currentLanguage) return;
        currentLanguage = lang;
        document.querySelectorAll('.language-switcher button').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
        });
        loadTranslations(lang).then(() => {
            updateContent();
        });
    }

    // Initialize with English
    loadTranslations('en').then(() => {
        updateContent();
    });

    // Expose changeLanguage function globally
    window.changeLanguage = changeLanguage;

    // FAQ Interaction
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        item.addEventListener('toggle', () => {
            if (item.open) {
                faqItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.open) {
                        otherItem.open = false;
                    }
                });
            }
        });
    });
});