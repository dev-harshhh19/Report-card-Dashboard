document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('loginSection');
    const scorecardSection = document.getElementById('scorecardSection');
    const loginForm = document.getElementById('loginForm');
    const errorMsg = document.getElementById('errorMsg');

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

    // Auto-login with existing session (HttpOnly cookie)
    fetch('/dashboard?json=1').then(res => {
        if (res.ok) {
            res.json().then(student => {
                hideSection(loginSection);
                renderScorecard(student);
            });
        }
    });

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
        const hasData = student.semesters && student.semesters.length > 0;
        
        let dashboardContent = `
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h2 class="text-2xl font-bold text-blue-700">Welcome, <span class="capitalize">${student.username}</span></h2>
                    <p class="text-gray-600">Academic Survival Planner</p>
                </div>
                <button id="logoutBtn" class="px-4 py-2 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition" aria-label="Logout">Logout</button>
            </div>
        `;

        if (hasData) {
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
                    <td class="py-1 px-2">Sem ${sem.semester_number || (i + 1)}</td>
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

            dashboardContent += `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div>
                        <h3 class="text-lg font-semibold mb-2 text-gray-700">Subjects & Marks (Latest)</h3>
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
        } else {
            dashboardContent += `
                <div class="text-center py-8">
                    <p class="text-gray-600 mb-4">You haven't tracked any semesters yet.</p>
                </div>
            `;
        }

        // Add the manual entry form
        dashboardContent += `
            <div class="mt-8 border-t pt-6">
                <h3 class="text-xl font-bold text-blue-700 mb-4">Log New Semester</h3>
                <form id="addSemesterForm" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-gray-700 font-medium mb-1">Semester Number</label>
                            <input type="number" id="semNumber" min="1" max="10" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400">
                        </div>
                    </div>
                    <div class="space-y-3">
                        <label class="block text-gray-700 font-medium">Subjects and Marks (out of 100)</label>
                        ${Array(5).fill(0).map((_, i) => `
                            <div class="flex gap-4">
                                <input type="text" placeholder="Subject ${i+1} Name" required class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 subject-input">
                                <input type="number" placeholder="Marks" min="0" max="100" required class="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 mark-input">
                            </div>
                        `).join('')}
                    </div>
                    <div id="addErrorMsg" class="hidden text-red-600 text-sm font-semibold"></div>
                    <button type="submit" class="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition">Save Semester</button>
                </form>
            </div>
        `;

        scorecardSection.innerHTML = dashboardContent;
        showSection(scorecardSection);

        if (hasData) {
            setTimeout(() => {
                const radius = 48;
                const circ = 2 * Math.PI * radius;
                const percent = Math.min(100, Math.max(0, (student.sgpa / 10) * 100));
                
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
                        labels: student.semesters.map((s, i) => `Sem ${s.semester_number || (i+1)}`),
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
        }

        // Logout handler
        document.getElementById('logoutBtn').onclick = () => {
            fetch('/logout', { method: 'POST' }).then(() => {
                window.location.reload();
            });
        };

        // Add semester handler
        document.getElementById('addSemesterForm').onsubmit = (e) => {
            e.preventDefault();
            const semNum = document.getElementById('semNumber').value;
            const subInputs = document.querySelectorAll('.subject-input');
            const markInputs = document.querySelectorAll('.mark-input');
            const addErrorMsg = document.getElementById('addErrorMsg');
            
            const subjects = Array.from(subInputs).map(i => i.value);
            const marks = Array.from(markInputs).map(i => parseInt(i.value, 10));
            
            const payload = {
                semester_number: parseInt(semNum, 10),
                subjects: subjects,
                marks: marks
            };

            fetch('/add_semester', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(async res => {
                if (res.ok) {
                    showToast('Semester added successfully!');
                    // Reload dashboard
                    fetch('/dashboard?json=1').then(r => r.json()).then(studentData => renderScorecard(studentData));
                } else {
                    const data = await res.json();
                    addErrorMsg.textContent = data.error || 'Failed to add semester';
                    addErrorMsg.classList.remove('hidden');
                }
            }).catch(() => {
                addErrorMsg.textContent = 'Network error.';
                addErrorMsg.classList.remove('hidden');
            });
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

    window.showPolicy = function(type) {
        const modal = document.getElementById('policyModal');
        const title = document.getElementById('policyTitle');
        const content = document.getElementById('policyContent');
        modal.classList.remove('hidden');
        if (type === 'privacy') {
            title.textContent = 'Privacy Policy';
            content.innerHTML = 'We respect your privacy. No personal data is shared or sold. Data is stored securely.';
        } else if (type === 'security') {
            title.textContent = 'Security Policy';
            content.innerHTML = 'We use secure session handling with HTTP-only cookies and robust password hashing (scrypt).';
        } else if (type === 'terms') {
            title.textContent = 'Terms of Service';
            content.innerHTML = 'This platform is for educational tracking.';
        }
    };

    window.closePolicy = function() {
        document.getElementById('policyModal').classList.add('hidden');
    };

    window.showFeedback = function() {
        document.getElementById('feedbackModal').classList.remove('hidden');
        document.getElementById('feedbackMsg').classList.add('hidden');
    };

    window.closeFeedback = function() {
        document.getElementById('feedbackModal').classList.add('hidden');
    };

    window.submitFeedback = function(e) {
        e.preventDefault();
        document.getElementById('feedbackMsg').classList.remove('hidden');
        setTimeout(() => closeFeedback(), 1500);
    };

    // --- Chatbot Logic ---
    const chatbotBtn = document.getElementById('chatbotBtn');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const closeChatbot = document.getElementById('closeChatbot');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotMessages = document.getElementById('chatbotMessages');

    if (chatbotBtn && chatbotWindow) {
        chatbotBtn.addEventListener('click', () => {
            chatbotWindow.classList.remove('hidden');
            chatbotWindow.classList.add('flex');
            chatbotInput.focus();
        });

        closeChatbot.addEventListener('click', () => {
            chatbotWindow.classList.add('hidden');
            chatbotWindow.classList.remove('flex');
        });

        chatbotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatbotInput.value.trim();
            if (!message) return;

            // Add user message to UI
            addChatMessage(message, 'user');
            chatbotInput.value = '';
            
            const submitBtn = chatbotForm.querySelector('button');
            submitBtn.disabled = true;
            submitBtn.textContent = '...';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });
                
                const data = await response.json();
                if (response.ok) {
                    addChatMessage(data.response, 'bot');
                } else {
                    addChatMessage(data.error || 'Failed to get response.', 'bot', true);
                }
            } catch (error) {
                addChatMessage('Network error communicating with the assistant.', 'bot', true);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send';
            }
        });

        function addChatMessage(text, sender, isError = false) {
            const div = document.createElement('div');
            div.className = sender === 'user' 
                ? 'self-end bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2 max-w-[85%] shadow-sm'
                : `self-start ${isError ? 'bg-red-100 text-red-900' : 'bg-blue-50 text-blue-900'} rounded-2xl rounded-tl-sm px-4 py-2 max-w-[85%] shadow-sm`;
            div.textContent = text;
            chatbotMessages.appendChild(div);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }
    }
});
