document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('loginSection');
    const scorecardSection = document.getElementById('scorecardSection');
    const loginForm = document.getElementById('loginForm');
    const errorMsg = document.getElementById('errorMsg');
    const chatbotBtn = document.getElementById('chatbotBtn');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const closeChatbot = document.getElementById('closeChatbot');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotMessages = document.getElementById('chatbotMessages');
    // Toast notification
    let toast;
    function showToast(msg) {
        if (toast) toast.remove();
        toast = document.createElement('div');
        toast.className = 'fixed top-6 left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
        toast.setAttribute('role', 'status');
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => { toast.remove(); }, 2500);
    }
    // Helper: Animate show/hide
    function showSection(section) {
        section.classList.remove('hidden');
        section.classList.add('fade-in', 'slide-up');
        setTimeout(() => {
            const focusable = section.querySelector('input, button, [tabindex]:not([tabindex="-1"])');
            if (focusable) focusable.focus();
        }, 400);
    }
    function hideSection(section) {
        section.classList.add('hidden');
        section.classList.remove('fade-in', 'slide-up');
    }
    // SGPA motivational label
    function getMotivation(sgpa) {
        if (sgpa >= 9) return 'Outstanding! 🌟';
        if (sgpa >= 8) return 'Great job! Keep it up!';
        if (sgpa >= 7) return 'Good work! Aim higher!';
        if (sgpa >= 6) return 'You can do even better!';
        return "Don't give up! Every step counts!";
    }
    // Render the scorecard UI
    function renderScorecard(student) {
        // SVG ring params
        const radius = 48, stroke = 8, norm = 10;
        const percent = Math.min(100, Math.max(0, (student.sgpa / norm) * 100));
        const circ = 2 * Math.PI * radius;
        let color = '#22c55e'; // green
        if (student.sgpa < 6) color = '#ef4444'; // red
        else if (student.sgpa < 8) color = '#facc15'; // yellow
        // Semester table
        let semTable = `<table class="w-full text-sm mt-4 mb-2 border rounded overflow-hidden">
            <thead><tr class="bg-blue-50 text-blue-700">
                <th class="py-2 px-2">Semester</th>
                <th class="py-2 px-2">SGPA</th>
                <th class="py-2 px-2">Subjects & Marks</th>
                <th class="py-2 px-2">Total/500</th>
            </tr></thead><tbody>`;
        student.semesters.forEach((sem, i) => {
            let subjMarks = sem.subjects.map((subj, idx) => `<span class='whitespace-nowrap'>${subj}: <b>${sem.marks[idx]}</b></span>`).join('<br>');
            semTable += `<tr class="text-center ${i % 2 === 0 ? 'bg-white' : 'bg-blue-50'}">
                <td class="py-1 px-2">Sem ${i + 1}</td>
                <td class="py-1 px-2 font-bold">${sem.sgpa}</td>
                <td class="py-1 px-2">${subjMarks}</td>
                <td class="py-1 px-2 font-semibold">${sem.total} / 500</td>
            </tr>`;
        });
        semTable += '</tbody></table>';
        // Latest semester subject/marks
        let latestSem = student.semesters[student.semesters.length - 1];
        let latestSubjects = latestSem.subjects.map((subj, idx) => 
          `<li class="flex justify-between items-center bg-blue-50 rounded px-4 py-2">
            <span>${subj}</span>
            <span class="font-bold text-blue-700">${latestSem.marks[idx] ?? ''}</span>
          </li>`
        ).join('');
        scorecardSection.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-blue-700">Welcome, <span class="capitalize">${student.username}</span></h2>
                <button id="logoutBtn" class="px-4 py-2 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition" aria-label="Logout">Logout</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div>
                    <h3 class="text-lg font-semibold mb-2 text-gray-700">Subjects & Marks (Latest Semester)</h3>
                    <ul class="space-y-2">
                        ${latestSubjects}
                    </ul>
                    <div class="mt-2 text-right font-bold text-blue-700">Total: ${latestSem.total} / 500</div>
                    <div class="mt-6">
                        <h4 class="font-semibold text-blue-700 mb-1">All Semesters</h4>
                        ${semTable}
                    </div>
                </div>
                <div class="flex flex-col items-center justify-center">
                    <h3 class="text-lg font-semibold mb-2 text-gray-700">SGPA (Latest)</h3>
                    <div class="relative flex items-center justify-center mb-2" style="width:120px;height:120px;">
                        <svg width="120" height="120" class="block" aria-label="SGPA Progress Ring">
                            <circle cx="60" cy="60" r="${radius}" stroke="#e5e7eb" stroke-width="${stroke}" fill="none" />
                            <circle id="sgpaRing" cx="60" cy="60" r="${radius}" stroke="${color}" stroke-width="${stroke}" fill="none" stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ}" style="transition: stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1), stroke 0.5s;" />
                            <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="2.5rem" font-weight="bold" fill="#16a34a">${student.sgpa}</text>
                        </svg>
                    </div>
                    <div id="sgpaMotivation" class="text-center text-base font-semibold mt-1" style="color:${color}">${getMotivation(student.sgpa)}</div>
                </div>
            </div>
            <div>
                <h3 class="text-lg font-semibold mb-2 text-gray-700">Growth Over Time (SGPA)</h3>
                <canvas id="growthChart" height="120"></canvas>
            </div>
        `;
        showSection(scorecardSection);
        setTimeout(() => {
            // Animate SGPA ring
            const ring = document.getElementById('sgpaRing');
            if (ring) {
                ring.setAttribute('stroke-dashoffset', circ - (percent / 100) * circ);
            }
            // Chart.js growth chart
            const ctx = document.getElementById('growthChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: student.semesters.map((_, i) => `Sem ${i+1}`),
                    datasets: [{
                        label: 'SGPA',
                        data: student.semesters.map(s => s.sgpa),
                        borderColor: 'rgba(16,185,129,0.9)',
                        backgroundColor: 'rgba(16,185,129,0.2)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, max: 10 } }
                }
            });
        }, 200);
        // Logout handler
        document.getElementById('logoutBtn').onclick = () => {
            fetch('/logout', { method: 'POST' }).then(() => window.location.reload());
        };
    }

    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            errorMsg.classList.add('hidden');
            errorMsg.textContent = '';
            const formData = new FormData(loginForm);
            const loginBtn = loginForm.querySelector('button[type="submit"]');
            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            fetch('/login', { method: 'POST', body: formData })
                .then(async response => {
                    if (!response.ok) {
                        const data = await response.json();
                        errorMsg.textContent = data.error || 'Login failed. Please try again.';
                        errorMsg.classList.remove('hidden');
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Login';
                        errorMsg.focus();
                        return;
                    }
                    // Fetch student data as JSON
                    fetch('/dashboard?json=1').then(res => res.json()).then(student => {
                        hideSection(loginSection);
                        renderScorecard(student);
                        showToast('Login successful!');
                    });
                })
                .catch(() => {
                    errorMsg.textContent = 'Network error. Please try again.';
                    errorMsg.classList.remove('hidden');
                    loginBtn.disabled = false;
                    loginBtn.textContent = 'Login';
                    errorMsg.focus();
                });
        });
    }

    // Expanded testimonials carousel
    const testimonials = [
        { text: "“This platform made tracking my progress so easy and fun!”", author: "— Priya, Student" },
        { text: "“The growth chart is so motivating. Love the design!”", author: "— Rahul, Student" },
        { text: "“Simple, secure, and beautiful. Highly recommended!”", author: "— Mrs. Sharma, Teacher" },
        { text: "“I can finally see my academic journey at a glance.”", author: "— Aarav, Student" },
        { text: "“Education is the most powerful weapon which you can use to change the world.”", author: "— Nelson Mandela" },
        { text: "“Success is not the key to happiness. Happiness is the key to success.”", author: "— Albert Schweitzer" },
        { text: "“The future belongs to those who believe in the beauty of their dreams.”", author: "— Eleanor Roosevelt" },
        { text: "“The expert in anything was once a beginner.”", author: "— Helen Hayes" },
        { text: "“Don't let what you cannot do interfere with what you can do.”", author: "— John Wooden" },
        { text: "“Strive for progress, not perfection.”", author: "— Unknown" },
        { text: "“Learning never exhausts the mind.”", author: "— Leonardo da Vinci" },
        { text: "“The beautiful thing about learning is that no one can take it away from you.”", author: "— B.B. King" },
        { text: "“Success is the sum of small efforts, repeated day in and day out.”", author: "— Robert Collier" },
        { text: "“The only way to do great work is to love what you do.”", author: "— Steve Jobs" },
        { text: "“Opportunities don't happen, you create them.”", author: "— Chris Grosser" },
        { text: "“Push yourself, because no one else is going to do it for you.”", author: "— Unknown" },
        { text: "“Great things never come from comfort zones.”", author: "— Unknown" },
        { text: "“Dream bigger. Do bigger.”", author: "— Unknown" },
        { text: "“Don't watch the clock; do what it does. Keep going.”", author: "— Sam Levenson" },
        { text: "“The secret of getting ahead is getting started.”", author: "— Mark Twain" },
        { text: "“You don't have to be great to start, but you have to start to be great.”", author: "— Zig Ziglar" },
        { text: "“Believe you can and you're halfway there.”", author: "— Theodore Roosevelt" },
        { text: "“It always seems impossible until it's done.”", author: "— Nelson Mandela" },
        { text: "“Mistakes are proof that you are trying.”", author: "— Jennifer Lim" },
        { text: "“The harder you work for something, the greater you'll feel when you achieve it.”", author: "— Unknown" }
    ];
    let tIndex = 0;
    const testimonialText = document.getElementById('testimonialText');
    const testimonialAuthor = document.getElementById('testimonialAuthor');
    function showTestimonial(idx) {
        testimonialText.classList.remove('fade-in');
        testimonialAuthor.classList.remove('fade-in');
        setTimeout(() => {
            testimonialText.textContent = testimonials[idx].text;
            testimonialAuthor.textContent = testimonials[idx].author;
            testimonialText.classList.add('fade-in');
            testimonialAuthor.classList.add('fade-in');
        }, 150);
    }
    document.getElementById('prevTestimonial').onclick = () => {
        tIndex = (tIndex - 1 + testimonials.length) % testimonials.length;
        showTestimonial(tIndex);
    };
    document.getElementById('nextTestimonial').onclick = () => {
        tIndex = (tIndex + 1) % testimonials.length;
        showTestimonial(tIndex);
    };
    // Keyboard navigation for carousel
    document.getElementById('testimonialCarousel').addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') document.getElementById('prevTestimonial').click();
        if (e.key === 'ArrowRight') document.getElementById('nextTestimonial').click();
    });
    document.getElementById('testimonialCarousel').tabIndex = 0;

    // Chatbot logic
    const chatbotReplies = [
        "I'm here to help! Try asking about your SGPA or marks.",
        "You can view your growth chart after login.",
        "For privacy, your data is only visible to you.",
        "Contact harshadnikam@example.com for more support.",
        "Try refreshing the page if you face any issues.",
        "You can log out anytime using the logout button."
    ];
    function openChatbot() {
        chatbotWindow.style.display = 'flex';
        setTimeout(() => chatbotInput.focus(), 200);
    }
    function closeChatbotWindow() {
        chatbotWindow.style.display = 'none';
        chatbotBtn.focus();
    }
    chatbotBtn.onclick = openChatbot;
    closeChatbot.onclick = closeChatbotWindow;
    chatbotForm.onsubmit = (e) => {
        e.preventDefault();
        const msg = chatbotInput.value.trim();
        if (!msg) return;
        // Append user message
        const userMsg = document.createElement('div');
        userMsg.className = 'self-end bg-blue-500 text-white rounded-lg px-3 py-2 max-w-[80%]';
        userMsg.textContent = msg;
        chatbotMessages.appendChild(userMsg);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        chatbotInput.value = '';
        // Simulate assistant reply
        setTimeout(() => {
            const botMsg = document.createElement('div');
            botMsg.className = 'self-start bg-blue-100 rounded-lg px-3 py-2 max-w-[80%]';
            botMsg.textContent = chatbotReplies[Math.floor(Math.random() * chatbotReplies.length)];
            chatbotMessages.appendChild(botMsg);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }, 700);
    };
    // Keyboard accessibility for chatbot
    chatbotWindow.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeChatbotWindow();
        if (e.key === 'Tab') {
            // Focus trap
            const focusable = chatbotWindow.querySelectorAll('input, button');
            const first = focusable[0], last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault(); last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault(); first.focus();
            }
        }
    });
});
